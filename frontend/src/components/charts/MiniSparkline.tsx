import { LineChart, Line, ResponsiveContainer } from 'recharts'

interface Props { data?: number[]; color?: string; height?: number }

export default function MiniSparkline({ data = [], color = '#10b981', height = 32 }: Props) {
  const chartData = data.map((v, i) => ({ i, v }))
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData}>
        <Line type="monotone" dataKey="v" stroke={color} strokeWidth={1.5} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}
