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
    let yPosition = 20

    // Title
    pdf.setFontSize(18)
    pdf.text('Audio Classification Report', pageWidth / 2, yPosition, { align: 'center' })
    yPosition += 15

    // Recording info
    pdf.setFontSize(10)
    pdf.text(`File: ${recording.original_filename}`, 20, yPosition)
    yPosition += 7
    pdf.text(`Duration: ${recording.duration_sec.toFixed(1)}s`, 20, yPosition)
    yPosition += 7
    pdf.text(`Site: ${recording.site_id}, Hour: ${recording.hour}`, 20, yPosition)
    yPosition += 7
    pdf.text(`Date: ${new Date(recording.created_at).toLocaleString()}`, 20, yPosition)
    yPosition += 15

    // Top species
    pdf.setFontSize(12)
    pdf.text('Top Detected Species:', 20, yPosition)
    yPosition += 10

    pdf.setFontSize(9)
    ;(prediction?.top_species || []).slice(0, 5).forEach((sp, idx) => {
      const text = `${idx + 1}. ${sp.common_name} - ${(sp.max_score * 100).toFixed(1)}% (${sp.windows_detected} windows, ${sp.seconds_present?.toFixed(1) || 'N/A'}s)`
      pdf.text(text, 20, yPosition)
      yPosition += 7

      if (yPosition > pageHeight - 20) {
        pdf.addPage()
        yPosition = 20
      }
    })

    yPosition += 10

    // Try to capture heatmap or chart if visible
    try {
      const chartElement = document.getElementById('results-chart')
      if (chartElement) {
        pdf.setFontSize(12)
        pdf.text('Detection Heatmap:', 20, yPosition)
        yPosition += 10

        const canvas = await html2canvas(chartElement, {
          backgroundColor: '#1e293b',
          scale: 1,
        })
        const imgData = canvas.toDataURL('image/png')
        const imgWidth = pageWidth - 40
        const imgHeight = (canvas.height / canvas.width) * imgWidth
        if (imgHeight + yPosition > pageHeight - 20) {
          pdf.addPage()
          yPosition = 20
        }
        pdf.addImage(imgData, 'PNG', 20, yPosition, imgWidth, imgHeight)
      }
    } catch (err) {
      console.error('Failed to capture chart:', err)
    }

    // Save
    pdf.save(`${recording.id}_report.pdf`)
  }

  return (
    <div className="bg-navy-800 rounded-lg p-6 border border-navy-700 mb-8">
      <h2 className="text-xl font-bold text-white mb-4">Export Results</h2>

      <div className="flex flex-wrap gap-4">
        <button
          onClick={handleDownloadCSV}
          className="flex items-center gap-2 py-2 px-4 bg-green-600 hover:bg-green-700 text-white rounded font-medium transition"
        >
          <span>📊</span> Download CSV
        </button>

        <button
          onClick={handleDownloadPDF}
          className="flex items-center gap-2 py-2 px-4 bg-red-600 hover:bg-red-700 text-white rounded font-medium transition"
        >
          <span>📄</span> Download PDF Report
        </button>
      </div>

      <p className="text-navy-400 text-sm mt-3">
        CSV includes window-by-window detections and species summary. PDF includes report with top species and heatmap.
      </p>
    </div>
  )
}
