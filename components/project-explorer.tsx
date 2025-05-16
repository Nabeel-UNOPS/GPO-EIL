"use client"

import { useState, useEffect } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, Filter, Download, FileText, Info } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { sdgColors } from "@/lib/sdg-colors"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

interface ProjectExplorerProps {
  projects: any[]
  searchTerm: string
  setSearchTerm: (term: string) => void
  setReportProject: (project: any) => void
}

export function ProjectExplorer({ projects, searchTerm, setSearchTerm, setReportProject }: ProjectExplorerProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const [shuffledProjects, setShuffledProjects] = useState<any[]>([])
  const itemsPerPage = 10

  // Fisher-Yates shuffle algorithm
  const shuffleArray = (array: any[]) => {
    const newArray = [...array]
    for (let i = newArray.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [newArray[i], newArray[j]] = [newArray[j], newArray[i]]
    }
    return newArray
  }

  // Initialize shuffled projects on component mount only
  useEffect(() => {
    setShuffledProjects(shuffleArray(projects))
  }, [])

  // Update shuffled projects when projects change, but don't reshuffle
  useEffect(() => {
    if (shuffledProjects.length === 0) {
      setShuffledProjects(shuffleArray(projects))
    } else {
      // Update the project data without changing order
      const projectIds = shuffledProjects.map(p => p.id)
      const updatedShuffledProjects = projectIds.map(id => 
        projects.find(p => p.id === id)
      ).filter(Boolean)
      
      // If there are new projects that weren't in the original shuffle, add them at the end
      const existingIds = new Set(projectIds)
      const newProjects = projects.filter(p => !existingIds.has(p.id))
      
      setShuffledProjects([...updatedShuffledProjects, ...newProjects])
    }
  }, [projects])

  // Calculate pagination
  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentProjects = shuffledProjects.slice(indexOfFirstItem, indexOfLastItem)
  const totalPages = Math.ceil(shuffledProjects.length / itemsPerPage)

  // Generate page numbers
  const pageNumbers = []
  for (let i = 1; i <= totalPages; i++) {
    pageNumbers.push(i)
  }

  // Muted but colorful tool badge colors
  const toolColors = {
    Satellite: "#7c9eb2", // Muted blue
    "AI-Powered": "#a3b18a", // Muted green
    UAV: "#e5989b", // Muted pink
    Monitoring: "#b392ac", // Muted purple
    Dashboard: "#d4a373", // Muted tan
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
          <Input
            type="search"
            placeholder="Search projects..."
            className="pl-8 border-slate-200 bg-white"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        {/* <Button variant="outline" size="sm" className="flex items-center gap-1 border-slate-200">
          <Filter className="h-4 w-4" />
          Advanced Filters
        </Button> */}
        {/* <Button variant="outline" size="sm" className="flex items-center gap-1 border-slate-200">
          <Download className="h-4 w-4" />
          Export
        </Button> */}
      </div>

      <div className="rounded-md border border-slate-200 overflow-hidden bg-white shadow-sm">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader className="bg-slate-50">
              <TableRow>
                <TableHead className="font-semibold text-slate-700 w-[60px]">Engagement ID</TableHead>
                <TableHead className="font-semibold text-slate-700 w-[200px]">Engagement Description</TableHead>
                <TableHead className="font-semibold text-slate-700 w-[60px]">Region</TableHead>
                <TableHead className="font-semibold text-slate-700 w-[100px]">Mapped SDG</TableHead>
                <TableHead className="font-semibold text-slate-700 w-[100px]">
                  <div className="flex items-center gap-1">
                    SDG Indicators
                    <a 
                      href="https://unstats.un.org/sdgs/indicators/Global-Indicator-Framework-after-2025-review-English.pdf" 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="text-slate-500 hover:text-slate-700 transition-colors"
                      title="SDG Indicators Documentation"
                    >
                      <Info className="h-3.5 w-3.5" />
                    </a>
                  </div>
                </TableHead>
                <TableHead className="font-semibold text-slate-700 w-[150px]">Funding Source</TableHead>
                <TableHead className="font-semibold text-slate-700 w-[100px]">Project Manager</TableHead>
                <TableHead className="font-semibold text-slate-700 w-[100px]">Project Manager Email</TableHead>
                <TableHead className="font-semibold text-slate-700 w-[150px]">Proposed Remote Sensing Tools</TableHead>
                {/* <TableHead className="font-semibold text-slate-700 w-[60px]">Original File</TableHead> */}
                <TableHead className="font-semibold text-slate-700 w-[60px]">Report</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {currentProjects.length > 0 ? (
                currentProjects.map((project, idx) => {
                  // Limit to max 5 tools per project
                  const limitedTools = project.relevantTools.slice(0, 5)

                  return (
                    <TableRow key={`${project.id}-${idx}`} className="hover:bg-slate-50">

                      {/* Engagement Number */}
                      <TableCell className="text-slate-700">{project.id || "Unknown"}</TableCell>

                      {/* Engagement Description */}
                      <TableCell className="font-medium text-slate-800">
                        <div className="flex flex-wrap gap-1">
                          {project.name}
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Badge className="font-medium text-white bg-opacity-20 hover:bg-opacity-90"
                                  style={{
                                    backgroundColor: '#b3b3b3',
                                    boxShadow: "none",
                                  }}>
                                  Details
                                </Badge>
                              </TooltipTrigger>
                              <TooltipContent className='max-w-[600px]' style={{ maxWidth:600}}>
                                  <div className="font-semibold text-slate-500">Summary:</div>
                                  <div className="mb-2 font-light text-slate-500">{project.summary || 'No summary available'}</div>
                                  <div className="font-semibold text-slate-500">Objectives:</div>
                                  <div className="mb-2 font-light text-slate-500">{project.objectives || 'Not identified'}</div>
                                  <div className="font-semibold text-slate-500">Problems Addressed:</div>
                                  <div className="mb-2 font-light text-slate-500">{project.problems_addressed || 'Not identified'}</div>
                                  <div className="font-semibold text-slate-500">Beneficiaries:</div>
                                  <div className="mb-2 font-light text-slate-500">{project.beneficiaries || 'Not identified'}</div>
                                  <div className="font-semibold text-slate-500">Anticipated Outcomes:</div>
                                  <div className="mb-2 font-light text-slate-500">{project.anticipated_outcomes || 'Not identified'}</div>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                      </TableCell>

                      {/* Region */}
                      <TableCell className="text-slate-700">{project.region || "Unknown"}</TableCell>

                      {/* SDG Goals */}
                      <TableCell>
                        <TooltipProvider>
                          <div className="flex flex-wrap gap-1">
                            {Array.isArray(project.sdg_goals) && project.sdg_goals.length > 0 ? (
                              project.sdg_goals.map((sdg: { sdg_goal?: string; name?: string; relevance?: string }, idx: number) => (
                                <Tooltip key={idx}>
                                  <TooltipTrigger asChild>
                                    <Badge className="font-medium text-white bg-opacity-100 hover:bg-opacity-100 hover:outline hover:outline-1 hover:outline-offset-1"
                                      style={{
                                        backgroundColor: sdg.sdg_goal && !isNaN(Number(sdg.sdg_goal)) ? `${sdgColors[Number(sdg.sdg_goal) - 1]}99` : '#b3b3b3',
                                        boxShadow: "none",
                                        cursor: "help"
                                      }}
                                    >
                                      SDG #{sdg.sdg_goal}
                                    </Badge>
                                  </TooltipTrigger>
                                  <TooltipContent className='max-w-[400px]' style={{ maxWidth:400}}>
                                    <div className="font-semibold text-slate-500">Name:</div>
                                    <div className="mb-2 font-light text-slate-500">{sdg.name}</div>
                                    <div className="font-semibold text-slate-500">Relevance:</div>
                                    <div className="mb-2 font-light text-slate-500">{sdg.relevance}</div>
                                  </TooltipContent>
                                </Tooltip>
                              ))
                            ) : (
                              <Badge className="font-medium text-white bg-slate-400" style={{ cursor: "default" }}>No SDG</Badge>
                            )}
                          </div>
                        </TooltipProvider>
                      </TableCell>

                      {/* SDG Indicators */}
                      <TableCell>
                        <TooltipProvider>
                          <div className="flex flex-wrap gap-1">
                            {Array.isArray(project.sdg_indicators) && project.sdg_indicators.length > 0 ? (
                              project.sdg_indicators.map((indicator: { sdg_indicator?: string; description?: string; measurability?: string }, idx: number) => (
                                <Tooltip key={idx}>
                                  <TooltipTrigger asChild>
                                    <Badge
                                      className="font-medium text-white bg-opacity-100 hover:bg-opacity-100 hover:outline hover:outline-1 hover:outline-offset-1"
                                      style={{
                                        backgroundColor: '#D4D4D4',
                                        boxShadow: "none",
                                        cursor: "help"
                                      }}
                                    >
                                      {indicator.sdg_indicator}
                                    </Badge>
                                  </TooltipTrigger>
                                  <TooltipContent className='max-w-[400px]' style={{ maxWidth:400}}>
                                    <div className="font-semibold text-slate-500">Description:</div>
                                    <div className="mb-2 text-slate-500">{indicator.description || 'No description'}</div>
                                    <div className="font-semibold text-slate-500">Measurability:</div>
                                    <div className="mb-2 text-slate-500">{indicator.measurability || 'No measurability info'}</div>
                                  </TooltipContent>
                                </Tooltip>
                              ))
                            ) : (
                              <Badge className="font-medium text-white bg-slate-400" style={{ cursor: "default" }}>No Indicator</Badge>
                            )}
                          </div>
                        </TooltipProvider>
                      </TableCell>

                      {/* Hub */}
                      {/* <TableCell className="text-slate-700">{project.file_url || "Unknown"}</TableCell> */}
                      
                      {/* Funding Source */}
                      <TableCell className="text-slate-700">{project.donor || project.fundingSource || "Unknown"}</TableCell>

                      {/* Project Manager */}
                      <TableCell className="text-slate-700">{project.projectManager}</TableCell>

                      {/* Project Manager Email */}
                      <TableCell className="text-slate-700">
                        <a href={`mailto:${project.projectManagerEmail}`} className="text-blue-600 hover:underline">
                          {project.projectManagerEmail}
                        </a>
                      </TableCell>

                      {/* Relevant Tools */}
                      <TableCell>
                        <TooltipProvider>
                          <div className="flex flex-wrap gap-1">
                            {limitedTools.map((tool: any, index: number) => {
                              // Get color for this tool
                              const bgColor = "#B4B4B4"

                              return (
                                <Tooltip key={index}>
                                  <TooltipTrigger asChild>
                                    <Badge
                                      className="text-xs text-white bg-opacity-20 hover:bg-opacity-90"
                                      style={{
                                        backgroundColor: bgColor,
                                        boxShadow: "none",
                                        cursor: "help"
                                      }}
                                    >
                                      {tool.name}
                                    </Badge>
                                  </TooltipTrigger>
                                  <TooltipContent className="max-w-xs">
                                    <div className="font-medium">{tool.name}</div>
                                    <div className="mt-1 text-s text-slate-500">
                                      <span className="font-semibold">Why this is a good fit:</span> {tool.rationale}
                                    </div>
                                    {tool.project_description_context && (
                                      <div className="mt-1 text-s text-slate-500">
                                        <span className="font-semibold">Context from project description:</span> {tool.project_description_context}
                                      </div>
                                    )}
                                  </TooltipContent>
                                </Tooltip>
                              )
                            })}
                          </div>
                        </TooltipProvider>
                      </TableCell>

                      {/* Original File */}
                      {/* <TableCell>
                        <div className="flex justify-center">
                          {project.file_url ? (
                            <a href={project.file_url} target="_blank" rel="noopener noreferrer">
                              <FileText className="h-5 w-5 text-blue-600 hover:text-blue-800 cursor-pointer" />
                            </a>
                          ) : (
                            <FileText className="h-5 w-5 text-slate-500 cursor-not-allowed" />
                          )}
                        </div>
                      </TableCell> */}

                      {/* Generate Report Button - */}
                      <TableCell>
                        <Button size="sm" variant="outline" onClick={() => setReportProject(project)}>
                          View
                        </Button>
                      </TableCell>

                    </TableRow>
                  )
                })
              ) : (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-slate-500">
                    No projects found matching your criteria
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {totalPages > 1 && (
        <Pagination className="mt-4">
          <PaginationContent>
            <PaginationItem>
              <PaginationPrevious
                href="#"
                onClick={(e) => {
                  e.preventDefault()
                  if (currentPage > 1) setCurrentPage(currentPage - 1)
                }}
                className={currentPage === 1 ? "pointer-events-none opacity-50" : ""}
              />
            </PaginationItem>

            {pageNumbers.map((number) => {
              // Show only first 5 pages, last 5 pages, and current page
              const showFirstPages = number <= 5;
              const showLastPages = number > totalPages - 2;
              const showCurrentPage = Math.abs(currentPage - number) <= 1; // Show pages near current page
              
              // Show ellipsis after page 5 if there are more than 10 pages
              const showFirstEllipsis = number === 6 && totalPages > 10;
              // Show ellipsis before the last 5 pages if there are more than 10 pages
              const showLastEllipsis = number === totalPages - 3 && totalPages > 10;
              
              if (showFirstPages || showLastPages || showCurrentPage) {
                return (
                  <PaginationItem key={number}>
                    <PaginationLink
                      href="#"
                      onClick={(e) => {
                        e.preventDefault()
                        setCurrentPage(number)
                      }}
                      isActive={currentPage === number}
                    >
                      {number}
                    </PaginationLink>
                  </PaginationItem>
                );
              } else if (showFirstEllipsis || showLastEllipsis) {
                return (
                  <PaginationItem key={`ellipsis-${number}`}>
                    <PaginationEllipsis />
                  </PaginationItem>
                );
              }
              
              return null;
            })}

            <PaginationItem>
              <PaginationNext
                href="#"
                onClick={(e) => {
                  e.preventDefault()
                  if (currentPage < totalPages) setCurrentPage(currentPage + 1)
                }}
                className={currentPage === totalPages ? "pointer-events-none opacity-50" : ""}
              />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      )}

      <div className="text-sm text-slate-500 mt-2">
        Showing {indexOfFirstItem + 1}-{Math.min(indexOfLastItem, shuffledProjects.length)} of {shuffledProjects.length} projects
      </div>
    </div>
  )
}
