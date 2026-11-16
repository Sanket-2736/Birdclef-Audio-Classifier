import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function ScoreChart({ prediction, selectedSpecies }) {
  const windows = prediction?.windows || []
  const validWindows = windows.filter((w) => !w.is_padding)

  // Build data for chart
  const chartData = validWindows.map((window, idx) => {
    const data = {
      time: (idx * 5).toFixed(0) + 's',
      window: idx,
    }

    // Get top 5 species across all windows
    if (window.top_k) {
      window.top_k.slice(0, 5).forEach((sp) => {
        data[sp.code] = sp.score
      })
    }

    return data
  })

  // Get all unique species codes
  const allSpecies = new Set()
  validWindows.forEach((w) => {
    if (w.top_k) {
      w.top_k.forEach((sp) => allSpecies.add(sp.code))
    }
  })
  const topSpecies = Array.from(allSpecies).slice(0, 5)

  const colors = [
    '#4b9fc9',
    '#ef4444',
    '#10b981',
    '#f59e0b',
    '#8b5cf6',
  ]

  return (
    <div className="bg-white rounded-none-none p-6 border-2 border-[#171717] shadow-[5px_5px_0_#171717] mb-8">
      <h2 className="text-2xl font-black tracking-tight text-[#171717] mb-6">Detection Score Over Time</h2>

      <div className="h-80 bg-[#fff3d6] rounded-none-none">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 10 }}>
            <defs>
              {topSpecies.map((code, idx) => (
                <linearGradient
                  key={`gradient-${code}`}
                  id={`color-${code}`}
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop offset="5%" stopColor={colors[idx]} stopOpacity={0.8} />
                  <stop offset="95%" stopColor={colors[idx]} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#171717" vertical={false} />

            <XAxis
              dataKey="time"
              stroke="#514a40"
              tick={{ fontSize: 12 }}
              axisLine={{ stroke: '#171717' }}
            />

            <YAxis
              stroke="#514a40"
              tick={{ fontSize: 12 }}
              domain={[0, 1]}
              label={{
                value: 'Confidence',
                angle: -90,
                position: 'insideLeft',
                fill: '#514a40',
              }}
              axisLine={{ stroke: '#171717' }}
            />

            <Tooltip
              contentStyle={{
                backgroundColor: '#fff8e8',
                border: '1px solid #171717',
                borderRadius: '0.5rem',
              }}
              labelStyle={{ color: '#171717' }}
              formatter={(value) => (value ? (value * 100).toFixed(1) + '%' : '-')}
            />

            <Legend wrapperStyle={{ paddingTop: '1rem' }} />

            {topSpecies.map((code, idx) => (
              <Area
                key={code}
                type="monotone"
                dataKey={code}
                stroke={colors[idx]}
                fillOpacity={selectedSpecies === code ? 0.8 : 0.3}
                fill={`url(#color-${code})`}
                stackId="1"
                strokeWidth={selectedSpecies === code ? 2 : 1}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <p className="text-[#766d5e] text-xs mt-4">
        Showing top 5 species. Non-padding windows only (each 5 seconds).
      </p>
    </div>
  )
}
