"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { sdgColors } from "@/lib/sdg-colors"

interface Project {
  id: number
  name: string
  region: string
  sdg: string
  status: string
  funding: number
}

interface Location {
  region: string
  x: number
  y: number
  projects: Project[]
}

interface WorldMapProps {
  projects: Project[]
}

export function WorldMap({ projects }: WorldMapProps) {
  const [hoveredLocation, setHoveredLocation] = useState<Location | null>(null)

  // Define static locations for regions
  const initialLocations: Location[] = [
    // Africa
    { region: "Africa", x: 500, y: 350, projects: [] },
    { region: "Africa", x: 520, y: 320, projects: [] },
    { region: "Africa", x: 480, y: 380, projects: [] },
    { region: "Africa", x: 450, y: 340, projects: [] },

    // Asia
    { region: "Asia", x: 700, y: 250, projects: [] },
    { region: "Asia", x: 750, y: 220, projects: [] },
    { region: "Asia", x: 680, y: 280, projects: [] },
    { region: "Asia", x: 730, y: 300, projects: [] },

    // Europe
    { region: "Europe", x: 520, y: 200, projects: [] },
    { region: "Europe", x: 490, y: 180, projects: [] },
    { region: "Europe", x: 540, y: 170, projects: [] },

    // Latin America and Caribbean
    { region: "Latin America and Caribbean", x: 300, y: 350, projects: [] },
    { region: "Latin America and Caribbean", x: 280, y: 380, projects: [] },
    { region: "Latin America and Caribbean", x: 320, y: 320, projects: [] },

    // Middle East
    { region: "Middle East", x: 580, y: 250, projects: [] },
    { region: "Middle East", x: 560, y: 270, projects: [] },

    // North America
    { region: "North America", x: 250, y: 200, projects: [] },
    { region: "North America", x: 220, y: 220, projects: [] },
    { region: "North America", x: 280, y: 180, projects: [] },

    // Oceania
    { region: "Oceania", x: 800, y: 400, projects: [] },
    { region: "Oceania", x: 820, y: 420, projects: [] },
  ]

  // Distribute projects into location dots
  const projectLocations: Location[] = initialLocations.map((loc) => ({ ...loc, projects: [] }))
  projects.forEach((project) => {
    const regionLocations = projectLocations.filter((loc) => loc.region === project.region)
    if (regionLocations.length > 0) {
      const index = project.id % regionLocations.length
      regionLocations[index].projects.push(project)
    }
  })

  return (
    <div className="relative h-[400px] w-full rounded-md overflow-hidden border border-slate-200 bg-white">
      <div className="absolute inset-0">
        <img src="/images/world-map.png" alt="World Map" className="w-full h-full object-cover" />

        {projectLocations.map((location, index) => {
          if (location.projects.length === 0) return null

          const dotSize = Math.min(10, Math.max(5, Math.log2(location.projects.length + 1) * 3))
          const firstProject = location.projects[0]
          const sdgNumber = parseInt(firstProject.sdg.match(/\d+/)?.[0] || "1")
          const color = sdgColors[sdgNumber - 1] || "#8884d8"

          return (
            <div
              key={`location-${index}`}
              className="absolute rounded-full cursor-pointer transform hover:scale-125 transition-transform"
              style={{
                left: `${(location.x / 1000) * 100}%`,
                top: `${(location.y / 500) * 100}%`,
                width: `${dotSize}px`,
                height: `${dotSize}px`,
                backgroundColor: color,
                boxShadow: "0 0 0 2px rgba(255, 255, 255, 0.8), 0 0 4px rgba(0, 0, 0, 0.2)",
                zIndex: 10,
              }}
              onMouseEnter={() => setHoveredLocation(location)}
              onMouseLeave={() => setHoveredLocation(null)}
            />
          )
        })}

        {hoveredLocation && (
          <Card
            className="absolute p-0 bg-white shadow-lg z-20 border-0 rounded-md overflow-hidden"
            style={{
              ...(() => {
                const xPercent = (hoveredLocation.x / 1000) * 100
                const yPercent = (hoveredLocation.y / 500) * 100
                const rightSide = xPercent > 70
                const bottomSide = yPercent > 60

                return {
                  left: rightSide ? "auto" : `${xPercent + 1}%`,
                  right: rightSide ? `${100 - xPercent + 1}%` : "auto",
                  top: bottomSide ? "auto" : `${yPercent + 1}%`,
                  bottom: bottomSide ? `${100 - yPercent + 1}%` : "auto",
                  transform: `translate(${rightSide ? "-10px" : "10px"}, ${bottomSide ? "-10px" : "10px"})`,
                  maxWidth: "300px",
                  maxHeight: "180px",
                }
              })(),
            }}
          >
            <div className="bg-blue-600 text-white text-xs font-medium p-2">
              {hoveredLocation.region} – {hoveredLocation.projects.length} Projects
            </div>
            <CardContent className="p-3 text-xs space-y-1.5 bg-white overflow-auto" style={{ maxHeight: "120px" }}>
              {hoveredLocation.projects.slice(0, 5).map((project, idx) => (
                <div key={idx} className="border-b border-slate-100 pb-2 last:border-0 last:pb-0">
                  <p className="font-bold text-sm">{project.name}</p>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-1">
                    <div className="text-slate-500">SDG:</div>
                    <div className="font-medium">{project.sdg.split(" ").slice(0, 2).join(" ")}</div>

                    <div className="text-slate-500">Status:</div>
                    <div className="font-medium">{project.status}</div>

                    <div className="text-slate-500">Funding:</div>
                    <div className="font-medium">${project.funding.toLocaleString()}</div>
                  </div>
                </div>
              ))}
              {hoveredLocation.projects.length > 5 && (
                <div className="text-center text-slate-500 pt-1">
                  + {hoveredLocation.projects.length - 5} more projects
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
