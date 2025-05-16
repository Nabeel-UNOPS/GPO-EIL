"use client"

import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, Cell } from "recharts"
import { Card, CardContent } from "@/components/ui/card"
import { sdgColors } from "@/lib/sdg-colors"

interface SdgSummaryProps {
  projects: any[]
  sdgs: any[]
}

export function SdgSummary({ projects, sdgs }: SdgSummaryProps) {
  // Count projects per SDG
  const sdgCounts = sdgs
    .map((sdg) => {
      const count = projects.filter((project) => project.sdg === sdg.name).length
      return {
        name: sdg.name,
        count: count,
        shortName: sdg.shortName,
      }
    })
    .sort((a, b) => b.count - a.count)

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={sdgCounts} layout="vertical" margin={{ top: 10, right: 10, left: 70, bottom: 20 }}>
          <XAxis type="number" stroke="#64748b" fontSize={12} tickLine={false} axisLine={{ stroke: "#e2e8f0" }} />
          <YAxis
            type="category"
            dataKey="shortName"
            tick={{ fontSize: 12 }}
            width={60}
            stroke="#64748b"
            tickLine={false}
            axisLine={{ stroke: "#e2e8f0" }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload
                return (
                  <Card className="border shadow-sm">
                    <CardContent className="p-3">
                      <div className="text-sm font-medium">{data.name}</div>
                      <div className="text-xs text-slate-500 mt-1">
                        Projects: <span className="font-semibold text-slate-700">{data.count}</span>
                      </div>
                    </CardContent>
                  </Card>
                )
              }
              return null
            }}
          />
          <Bar dataKey="count" radius={[4, 4, 4, 4]}>
            {sdgCounts.map((entry, index) => {
              const sdgNumber = Number.parseInt(entry.shortName.replace("SDG ", ""))
              return (
                <Cell
                  key={`cell-${index}`}
                  fill={sdgColors[sdgNumber - 1] || "#8884d8"}
                  stroke="white"
                  strokeWidth={1}
                />
              )
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
