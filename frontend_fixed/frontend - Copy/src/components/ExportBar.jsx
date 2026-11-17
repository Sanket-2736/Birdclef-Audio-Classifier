import { jsPDF } from 'jspdf'
import html2canvas from 'html2canvas'

export default function ExportBar({ recording, prediction, selectedChart }) {
  const handleDownloadCSV = () => {
    let csv = 'Window,Time,Duration (s),Top Species,Score,Taxon\n'

    const windows = prediction?.windows || []
    const validWindows = windows.filter((w) => !w.is_padding)

    validWindows.forEach((window, idx) => {
      const startTime = idx * 5
      const endTime = Math.min((idx + 1) * 5, prediction.real_duration_sec)

      if (window.top_k && window.top_k.length > 0) {
        window.top_k.forEach((sp) => {
          csv += `${idx},"${startTime}-${endTime}",${endTime - startTime},"${sp.name}",${sp.score.toFixed(4)},${sp.taxon}\n`
        })
      }
    })

    // Add top species summary
    csv += '\n\nTOP SPECIES SUMMARY\n'
    csv += 'Species,Common Name,Max Score,Mean Score,Windows Detected,Seconds Present\n'

    ;(prediction?.top_species || []).forEach((sp) => {
      csv += `"${sp.code}","${sp.common_name}",${sp.max_score.toFixed(4)},${sp.mean_score.toFixed(4)},${sp.windows_detected},${sp.seconds_present?.toFixed(2) || 'N/A'}\n`
    })

    // Download
    const element = document.createElement('a')
    element.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv))
    element.setAttribute('download', `${recording.id}_detections.csv`)
    element.style.display = 'none'
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  const handleDownloadPDF = async () => {
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const margin = 15
    const contentWidth = pageWidth - 2 * margin
    let yPosition = margin

    // ============================================================
    // HEADER SECTION
    // ============================================================
    
    // WildEcho branding
    pdf.setTextColor(52, 168, 219) // Blue
    pdf.setFontSize(24)
    pdf.text('WildEcho', margin, yPosition)
    pdf.setTextColor(0, 0, 0)
    
    pdf.setFontSize(9)
    pdf.text('Audio Biomonitoring Report', margin, yPosition + 7)
    
    // Divider
    pdf.setDrawColor(100, 100, 100)
    pdf.line(margin, yPosition + 10, pageWidth - margin, yPosition + 10)
    yPosition += 18

    // ============================================================
    // RECORDING METADATA
    // ============================================================
    
    pdf.setFontSize(11)
    pdf.setFont(undefined, 'bold')
    pdf.text('RECORDING INFORMATION', margin, yPosition)
    yPosition += 8
    
    pdf.setFont(undefined, 'normal')
    pdf.setFontSize(9)
    
    const recInfo = [
      [`File:`, recording.original_filename],
      [`Duration:`, `${recording.duration_sec.toFixed(2)}s`],
      [`Site ID:`, `${recording.site_id}`],
      [`Hour:`, `${recording.hour}:00`],
      [`Recorded:`, new Date(recording.created_at).toLocaleString()],
      [`Recording ID:`, recording.id],
    ]
    
    recInfo.forEach(([label, value]) => {
      pdf.setFont(undefined, 'bold')
      pdf.text(label, margin, yPosition)
      pdf.setFont(undefined, 'normal')
      pdf.text(value, margin + 30, yPosition)
      yPosition += 5
    })

    if (recording.lat && recording.lng) {
      pdf.setFont(undefined, 'bold')
      pdf.text('Location:', margin, yPosition)
      pdf.setFont(undefined, 'normal')
      pdf.text(`${recording.lat.toFixed(4)}, ${recording.lng.toFixed(4)}`, margin + 30, yPosition)
      yPosition += 5
    }

    yPosition += 5

    // ============================================================
    // ANALYSIS SUMMARY STATS
    // ============================================================
    
    pdf.setFontSize(11)
    pdf.setFont(undefined, 'bold')
    pdf.text('ANALYSIS SUMMARY', margin, yPosition)
    yPosition += 8

    const topSpecies = prediction?.top_species || []
    
    // Stats boxes
    const stats = [
      ['Species Detected', `${topSpecies.length}`],
      ['Valid Windows', `${prediction?.valid_windows || 0}`],
      ['Top Confidence', `${topSpecies.length > 0 ? (topSpecies[0].max_score * 100).toFixed(1) : 'N/A'}%`],
      ['Mean Confidence', `${topSpecies.length > 0 ? (topSpecies.reduce((a, sp) => a + sp.mean_score, 0) / topSpecies.length * 100).toFixed(1) : 'N/A'}%`],
    ]

    pdf.setFont(undefined, 'normal')
    pdf.setFontSize(8)
    
    let statsX = margin
    const statWidth = contentWidth / 2 - 2
    
    stats.forEach((stat, idx) => {
      const col = idx % 2
      const row = Math.floor(idx / 2)
      const x = margin + col * (statWidth + 4)
      const y = yPosition + row * 14

      // Box
      pdf.setDrawColor(200, 200, 200)
      pdf.rect(x, y, statWidth, 12)

      // Label
      pdf.setFont(undefined, 'bold')
      pdf.text(stat[0], x + 2, y + 4)

      // Value
      pdf.setFont(undefined, 'bold')
      pdf.setTextColor(25, 118, 210)
      pdf.setFontSize(10)
      pdf.text(stat[1], x + 2, y + 9)
      pdf.setTextColor(0, 0, 0)
      pdf.setFontSize(8)
    })

    yPosition += 30
    pdf.setFont(undefined, 'normal')

    // ============================================================
    // TOP SPECIES TABLE
    // ============================================================
    
    if (topSpecies.length > 0) {
      pdf.setFontSize(11)
      pdf.setFont(undefined, 'bold')
      pdf.text('TOP DETECTED SPECIES', margin, yPosition)
      yPosition += 8

      // Table header
      pdf.setFillColor(52, 168, 219)
      pdf.setTextColor(255, 255, 255)
      pdf.setFont(undefined, 'bold')
      pdf.setFontSize(8)

      const colWidths = [12, 50, 20, 20, 20, 20]
      const headers = ['#', 'Species', 'Max Score', 'Avg Score', 'Windows', 'Duration']
      let xPos = margin

      headers.forEach((h, i) => {
        pdf.rect(xPos, yPosition - 5, colWidths[i], 6, 'F')
        pdf.text(h, xPos + 1, yPosition - 1, { maxWidth: colWidths[i] - 2 })
        xPos += colWidths[i]
      })

      yPosition += 6
      pdf.setTextColor(0, 0, 0)
      pdf.setFont(undefined, 'normal')
      pdf.setFontSize(7.5)

      // Table rows
      topSpecies.slice(0, 10).forEach((sp, idx) => {
        if (yPosition > pageHeight - 20) {
          pdf.addPage()
          yPosition = margin
        }

        xPos = margin
        const rowData = [
          String(idx + 1),
          String(sp.common_name ?? 'Unknown'),
          `${(Number(sp.max_score || 0) * 100).toFixed(1)}%`,
          `${(Number(sp.mean_score || 0) * 100).toFixed(1)}%`,
          String(sp.windows_detected ?? 0),
          `${Number(sp.seconds_present || 0).toFixed(1)}s`,
        ]

        // Alternate row color
        if (idx % 2 === 0) {
          pdf.setFillColor(245, 245, 245)
          pdf.rect(margin, yPosition - 3.5, contentWidth, 5, 'F')
        }

        rowData.forEach((val, colIdx) => {
          pdf.text(val, xPos + 1, yPosition, { maxWidth: colWidths[colIdx] - 2 })
          xPos += colWidths[colIdx]
        })

        yPosition += 5
      })

      yPosition += 5
    }

    // ============================================================
    // TAXON BREAKDOWN
    // ============================================================
    
    const taxons = Array.from(new Set(topSpecies.map(sp => sp.taxon)))
    if (taxons.length > 0) {
      pdf.setFontSize(10)
      pdf.setFont(undefined, 'bold')
      pdf.text('SPECIES BY TAXON', margin, yPosition)
      yPosition += 7

      pdf.setFont(undefined, 'normal')
      pdf.setFontSize(8)

      taxons.forEach((taxon) => {
        const count = topSpecies.filter(sp => sp.taxon === taxon).length
        const pct = ((count / topSpecies.length) * 100).toFixed(1)
        
        pdf.text(`${taxon}: ${count} species (${pct}%)`, margin, yPosition)
        yPosition += 5
      })

      yPosition += 5
    }

    // ============================================================
    // CONFIDENCE DISTRIBUTION
    // ============================================================
    
    if (topSpecies.length > 0) {
      pdf.setFontSize(10)
      pdf.setFont(undefined, 'bold')
      pdf.text('CONFIDENCE SCORE DISTRIBUTION', margin, yPosition)
      yPosition += 7

      pdf.setFont(undefined, 'normal')
      pdf.setFontSize(7.5)

      const ranges = [
        { label: '90-100%', min: 0.9, max: 1.0, color: [6, 95, 70] },
        { label: '70-90%', min: 0.7, max: 0.9, color: [5, 150, 105] },
        { label: '50-70%', min: 0.5, max: 0.7, color: [16, 185, 129] },
        { label: '30-50%', min: 0.3, max: 0.5, color: [245, 158, 11] },
        { label: '<30%', min: 0, max: 0.3, color: [239, 68, 68] },
      ]

      ranges.forEach((range) => {
        const count = topSpecies.filter(sp => sp.max_score >= range.min && sp.max_score <= range.max).length
        const pct = ((count / topSpecies.length) * 100).toFixed(1)

        // Colored bar
        const barWidth = (count / topSpecies.length) * 40
        pdf.setFillColor(...range.color)
        pdf.rect(margin, yPosition - 2, barWidth, 3, 'F')

        pdf.setTextColor(0, 0, 0)
        pdf.text(`${range.label}: ${count} species (${pct}%)`, margin + 45, yPosition)

        yPosition += 4
      })

      yPosition += 5
    }

    // ============================================================
    // DETECTION METHODOLOGY
    // ============================================================
    
    if (yPosition > pageHeight - 40) {
      pdf.addPage()
      yPosition = margin
    }

    pdf.setFontSize(10)
    pdf.setFont(undefined, 'bold')
    pdf.text('ANALYSIS METHODOLOGY', margin, yPosition)
    yPosition += 7

    pdf.setFont(undefined, 'normal')
    pdf.setFontSize(8)
    
    const methodology = [
      '• Audio windowed into 5-second segments for analysis',
      '• Multiple machine learning models combined for robust detection',
      '• Species confidence scores represent model agreement',
      '• Detections filtered by temporal and spectral constraints',
      '• Results include both direct and indirect detections',
    ]

    methodology.forEach((line) => {
      const splitText = pdf.splitTextToSize(line, contentWidth - 5)
      splitText.forEach((text) => {
        pdf.text(text, margin + 2, yPosition)
        yPosition += 3.5
      })
    })

    yPosition += 5

    // ============================================================
    // FOOTER
    // ============================================================
    
    pdf.setFontSize(7)
    pdf.setTextColor(150, 150, 150)
    pdf.text(`Generated by WildEcho on ${new Date().toLocaleString()}`, margin, pageHeight - 5)
    pdf.text(`Report ID: ${recording.id.substring(0, 8)}`, pageWidth - margin - 40, pageHeight - 5)

    // Save
    pdf.save(`WildEcho_Report_${recording.id.substring(0, 8)}.pdf`)
  }

  return (
    <div className="bg-white rounded-none-none p-6 border-2 border-[#171717] shadow-[5px_5px_0_#171717] mb-8">
      <h2 className="text-xl font-black tracking-tight text-[#171717] mb-4">Export Results</h2>

      <div className="flex flex-wrap gap-4">
        <button
          onClick={handleDownloadCSV}
          className="flex items-center gap-2 py-2 px-4 bg-[#d9f4d2] hover:bg-[#c6e9be] text-[#171717] rounded-none font-bold border-2 border-[#171717] shadow-[3px_3px_0_#171717] transition hover:translate-x-[1px] hover:translate-y-[1px]"
        >
          <span>📊</span> Download CSV
        </button>

        <button
          onClick={handleDownloadPDF}
          className="flex items-center gap-2 py-2 px-4 bg-[#ffcfdb] hover:bg-[#ffb8ca] text-[#171717] rounded-none font-bold border-2 border-[#171717] shadow-[3px_3px_0_#171717] transition hover:translate-x-[1px] hover:translate-y-[1px]"
        >
          <span>📄</span> Download PDF Report
        </button>
      </div>

      <p className="text-[#766d5e] text-sm mt-3">
        <strong>CSV:</strong> Window-by-window detections and species summary.<br/>
        <strong>PDF:</strong> Comprehensive professional report with statistics, analysis methodology, and confidence distribution.
      </p>
    </div>
  )
}
