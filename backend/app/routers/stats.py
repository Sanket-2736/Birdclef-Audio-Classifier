"""
User statistics and dashboard endpoints.
"""

from datetime import datetime, timedelta
from typing import List
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from ..db import get_db
from ..db_models import User, Recording, Detection, Feedback
from ..routers.auth import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive user statistics for dashboard.
    
    Returns:
    - total_recordings
    - total_duration_sec
    - unique_species_count
    - uploads_per_day (last 30 days, zero-filled)
    - top_species (top 10 by windows_detected)
    - taxon_breakdown
    - life_list (all unique species with stats)
    - map_points (recordings with coordinates)
    """

    # Get user's recordings
    recordings = db.query(Recording).filter(
        Recording.user_id == current_user.id,
        Recording.status == "done",
    ).all()

    # 1. Basic stats
    total_recordings = len(recordings)
    total_duration_sec = sum(r.duration_sec for r in recordings) if recordings else 0.0

    # 2. Unique species count
    unique_species = db.query(Detection.species_code).filter(
        Detection.recording_id.in_([r.id for r in recordings] or [None]),
    ).distinct().count()

    # 3. Uploads per day (last 30 days)
    uploads_per_day = {}
    today = datetime.utcnow().date()
    for i in range(30):
        day = today - timedelta(days=i)
        uploads_per_day[day.isoformat()] = 0

    for recording in recordings:
        day = recording.created_at.date().isoformat()
        if day in uploads_per_day:
            uploads_per_day[day] += 1

    # Sort by date ascending
    uploads_per_day = dict(sorted(uploads_per_day.items()))

    # 4. Top species (by total windows_detected)
    top_species_query = db.query(
        Detection.species_code,
        Detection.species_name,
        Detection.taxon,
        func.sum(Detection.windows_detected).label("total_windows"),
        func.max(Detection.max_score).label("best_score"),
    ).filter(
        Detection.recording_id.in_([r.id for r in recordings] or [None]),
    ).group_by(
        Detection.species_code,
        Detection.species_name,
        Detection.taxon,
    ).order_by(
        desc("total_windows"),
    ).limit(10).all()

    top_species = [
        {
            "code": sp.species_code,
            "name": sp.species_name,
            "taxon": sp.taxon,
            "total_windows": sp.total_windows,
            "best_score": float(sp.best_score) if sp.best_score else 0.0,
        }
        for sp in top_species_query
    ]

    # 5. Taxon breakdown
    taxon_breakdown_query = db.query(
        Detection.taxon,
        func.count(func.distinct(Detection.species_code)).label("count"),
    ).filter(
        Detection.recording_id.in_([r.id for r in recordings] or [None]),
    ).group_by(Detection.taxon).all()

    taxon_breakdown = {
        tb.taxon: tb.count for tb in taxon_breakdown_query
    }

    # 6. Life list (all unique species)
    life_list_query = db.query(
        Detection.species_code,
        Detection.species_name,
        func.min(Recording.created_at).label("first_seen"),
        func.count(func.distinct(Detection.recording_id)).label("times_detected"),
        func.max(Detection.max_score).label("best_score"),
    ).join(
        Recording, Detection.recording_id == Recording.id
    ).filter(
        Recording.user_id == current_user.id,
        Recording.status == "done",
    ).group_by(
        Detection.species_code,
        Detection.species_name,
    ).all()

    # Get scientific names from Detections
    life_list = []
    for item in life_list_query:
        det = db.query(Detection).filter(
            Detection.species_code == item.species_code
        ).first()
        
        taxon = det.taxon if det else "Unknown"
        
        # Get most recent recording for this species
        most_recent = db.query(Recording).join(
            Detection, Recording.id == Detection.recording_id
        ).filter(
            Recording.user_id == current_user.id,
            Recording.status == "done",
            Detection.species_code == item.species_code,
        ).order_by(desc(Recording.created_at)).first()

        life_list.append({
            "species_code": item.species_code,
            "name": item.species_name,
            "scientific_name": getattr(det, "species_code", ""),  # Placeholder
            "taxon": taxon,
            "first_seen": item.first_seen.isoformat() if item.first_seen else None,
            "times_detected": item.times_detected,
            "best_score": float(item.best_score) if item.best_score else 0.0,
            "most_recent_recording_id": most_recent.id if most_recent else None,
        })

    # Sort by times_detected descending
    life_list = sorted(life_list, key=lambda x: x["times_detected"], reverse=True)

    # 7. Map points (recordings with coordinates)
    map_points = []
    for recording in recordings:
        if recording.lat is not None and recording.lng is not None:
            # Get top 3 species for this recording
            top_species_for_recording = db.query(
                Detection.species_name,
                Detection.max_score,
            ).filter(
                Detection.recording_id == recording.id,
            ).order_by(
                desc(Detection.max_score),
            ).limit(3).all()

            map_points.append({
                "recording_id": recording.id,
                "lat": float(recording.lat),
                "lng": float(recording.lng),
                "filename": recording.original_filename,
                "created_at": recording.created_at.isoformat(),
                "species": [
                    {"name": sp.species_name, "score": float(sp.max_score)}
                    for sp in top_species_for_recording
                ],
            })

    return {
        "total_recordings": total_recordings,
        "total_duration_sec": float(total_duration_sec),
        "unique_species_count": unique_species,
        "uploads_per_day": uploads_per_day,
        "top_species": top_species,
        "taxon_breakdown": taxon_breakdown,
        "life_list": life_list,
        "map_points": map_points,
    }


@router.get("/taxonomy")
async def get_taxonomy():
    """
    Get complete species taxonomy mapping from taxonomy.csv.
    
    Returns mapping of species codes to scientific names, common names, and taxon.
    This is used to generate proper Wikipedia and Xeno-canto links.
    """
    import csv
    from pathlib import Path
    
    # Load taxonomy
    backend_dir = Path(__file__).parent.parent.parent
    taxonomy_file = backend_dir / "taxonomy.csv"
    
    if not taxonomy_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Taxonomy file not found",
        )
    
    taxonomy = {}
    
    try:
        with open(taxonomy_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row['primary_label'].strip()
                taxonomy[code] = {
                    "scientific_name": row['scientific_name'].strip(),
                    "common_name": row['common_name'].strip(),
                    "taxon": row['class_name'].strip(),
                    "inat_id": row['inat_taxon_id'].strip(),
                }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading taxonomy: {str(e)}",
        )
    
    return {
        "total_species": len(taxonomy),
        "taxonomy": taxonomy,
    }
