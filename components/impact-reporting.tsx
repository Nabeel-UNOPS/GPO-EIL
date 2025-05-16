"use client"

import { Pie, PieChart, ResponsiveContainer, Cell, Tooltip, Legend } from "recharts"
import { Card, CardContent } from "@/components/ui/card"

interface ImpactReportingProps {
  projects: any[]
}

export function ImpactReporting({ projects }: ImpactReportingProps) {
  // Calculate reporting metrics
  const totalProjects = projects.length
  const projectsWithReports = projects.filter((p) => p.hasSubmittedReports).length
  const projectsWithoutReports = totalProjects - projectsWithReports
  const percentWithReports = totalProjects > 0 ? (projectsWithReports / totalProjects) * 100 : 0

  // Calculate average delay in reporting (mock data)
  const averageDelay = 12 // days

  // Calculate % projects missing reports
  const percentMissingReports = totalProjects > 0 ? (projectsWithoutReports / totalProjects) * 100 : 0

  // Calculate % projects with complete impact data
  const projectsWithCompleteData = projects.filter((p) => p.hasCompleteImpactData).length
  const percentWithCompleteData = totalProjects > 0 ? (projectsWithCompleteData / totalProjects) * 100 : 0

  // Data for pie chart
  const reportingData = [
    { name: "Submitted", value: projectsWithReports },
    { name: "Not Submitted", value: projectsWithoutReports },
  ]

  const COLORS = ["#4ade80", "#f87171"]

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="md:col-span-1 bg-white rounded-lg p-4 border border-slate-100 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-700 mb-2">Report Submission Status</h3>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={reportingData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {reportingData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="#fff" strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value, name) => [`${value} projects`, name]}
                contentStyle={{
                  backgroundColor: "white",
                  border: "1px solid #e2e8f0",
                  borderRadius: "4px",
                  boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
                }}
              />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value, entry, index) => <span style={{ color: "#64748b", fontWeight: 500 }}>{value}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="md:col-span-2">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 h-full">
          <Card className="shadow-sm border-slate-200">
            <CardContent className="p-6 flex flex-col items-center justify-center h-full">
              <div className="text-4xl font-bold text-amber-500">{averageDelay}</div>
              <div className="text-sm text-center text-slate-600 mt-2">Average delay in reporting (days)</div>
              <div className="mt-4 text-xs text-slate-500 text-center">Based on {totalProjects} active projects</div>
            </CardContent>
          </Card>

          <Card className="shadow-sm border-slate-200">
            <CardContent className="p-6 flex flex-col items-center justify-center h-full">
              <div className="text-4xl font-bold text-red-500">{percentMissingReports.toFixed(1)}%</div>
              <div className="text-sm text-center text-slate-600 mt-2">Projects missing reports</div>
              <div className="mt-4 text-xs text-slate-500 text-center">
                {projectsWithoutReports} out of {totalProjects} projects
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm border-slate-200">
            <CardContent className="p-6 flex flex-col items-center justify-center h-full">
              <div className="text-4xl font-bold text-green-500">{percentWithCompleteData.toFixed(1)}%</div>
              <div className="text-sm text-center text-slate-600 mt-2">Projects with complete impact data</div>
              <div className="mt-4 text-xs text-slate-500 text-center">
                {projectsWithCompleteData} out of {totalProjects} projects
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
