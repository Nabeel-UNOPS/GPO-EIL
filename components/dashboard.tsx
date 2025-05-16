"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Filter, Download, Info } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ProjectExplorer } from "@/components/project-explorer"
import { RemoteSensingTools } from "@/components/remote-sensing-tools"
import { SdgImpactGraph } from "@/components/sdg-impact-graph";
import { FundingSourceBar } from "@/components/funding-source-bar";
import { ImprovedLoadingScreen } from "@/components/loading-screen";
import { ProjectReportModal } from "./project-report-modal"


// Define types for our project data
type Project = {
  // Core project identifiers
  id: string;
  name: string;
  
  // Legal and administrative details BQ
  legal_agreement?: string;
  file_url?: string;
  region: string;
  hub?: string;
  donor?: string;
  
  // Project management contacts BQ
  projectManager: string;
  projectManagerEmail: string;
  deputyProjectManager?: string;
  deputyProjectManagerEmail?: string;
  // Funding Source BQ
  fundingSource: string;
  
  // Project details generated from LLM
  summary?: string;
  objectives?: string;
  problems_addressed?: string;
  beneficiaries?: string;
  anticipated_outcomes?: string;
  
  // SDG information
  sdg_goals?: Array<{
    sdg_goal?: string;
    name?: string;
    relevance?: string;
  }>;
  sdg_indicators?: Array<{
    sdg_indicator?: string;
    description?: string;
    measurability?: string;
  }>;
  
  // Tools and outcomes
  relevantTools: Array<{
    name: string;
    rationale: string;
    project_description_context: string;
  }>;
  quantifiable_outcomes?: string[];
  quantifiable_outcome_list?: Array<{
    outcome_item?: string;
  }>;
  remote_sensing_tools?: Array<{
    technology?: string;
    relevance_justification?: string;
    project_description_context?: string;
  }>;
};

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<string>("All");
  const [fundingSourceSearch, setFundingSourceSearch] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState("");
  const [reportProject, setReportProject] = useState<Project | null>(null);
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [selectedFunding, setSelectedFunding] = useState<string | null>(null);

  // Extract unique regions and funding sources from projects
  const regions = ["All", ...new Set(projects.map(p => p.region))];
  
  const TOOL_DESCRIPTIONS: { [key: string]: string } = {
    "Satellite Imagery & Geospatial Analysis": "●	Maxar Access: Provides high-resolution satellite imagery for damage assessment, land use analysis, and contamination detection. ●	Geospatial Data Processing: Uses GIS software (ArcGIS, QGIS) to analyze satellite images, terrain, and risk areas.",
    "Interactive Dashboards & Decision Support": "●	Geospatial Dashboards (Looker Studio, ArcGIS Online): Provides interactive visualizations of risk areas, EORE sessions, and explosive ordnance impact. ●	Predictive Analytics: Supports resource allocation and intervention strategies for mine action teams.",
    "Remote Monitoring & Early Warning": "●	Change Detection Analysis: Identifies shifts in terrain, infrastructure, or risk conditions over time. ●	Humanitarian Response Mapping: Supports rapid damage assessment and emergency response planning.",
    "AI-Powered Remote Sensing": "●	Machine Learning for Risk Mapping: AI models analyze past explosive ordnance incidents and predict high-risk areas. ●	Automated Object Detection: Identifies potential explosive ordnance, infrastructure damage, and changes in land use from satellite images.",
    "UAV & Aerial Data Integration": "●	Drone-based 3D Mapping: Generates high-resolution terrain models to assess affected areas. ●	Multi-Sensor Fusion: Combines satellite, UAV, and ground-based data for comprehensive analysis.",
  };

  // Filter projects based on selected filters
  const filteredProjects = projects.filter((project: any) => {
    const matchesRegion: boolean = selectedRegion === "All" || project.region === selectedRegion;
    const matchesFundingSource: boolean =
      fundingSourceSearch === "" || (project.donor?.toLowerCase() || "").includes(fundingSourceSearch.toLowerCase());
    const matchesSearch: boolean = searchTerm === "" || project.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTool: boolean = 
      !selectedTool || project.relevantTools.some((tool: any) => tool.name === selectedTool);
    const matchesFundingFilter: boolean = 
      !selectedFunding || project.donor === selectedFunding;

    return matchesRegion && matchesFundingSource && matchesSearch && matchesTool && matchesFundingFilter;
  });

  // Calculate tool counts based on filtered projects
  const includedToolNames = Object.keys(TOOL_DESCRIPTIONS);
  const toolCounts = filteredProjects.reduce((acc: any[], project) => {
    project.relevantTools.forEach(tool => {
      if (includedToolNames.includes(tool.name)) {
        const existingTool = acc.find(t => t.name === tool.name);
        if (existingTool) {
          existingTool.count++;
        } else {
          acc.push({
            name: tool.name,
            count: 1,
            description: TOOL_DESCRIPTIONS[tool.name] // use the placeholder
          });
        }
      }
    });
    return acc;
  }, []).sort((a, b) => b.count - a.count);

  const fundingSourceData = filteredProjects.reduce((acc: any[], project) => {
    if (project.donor && project.relevantTools.length > 0) {
      project.relevantTools.forEach(tool => {
        const fundingSource = project.donor || "Unknown";
        const existing = acc.find(f => f.name === fundingSource);
        if (existing) {
          existing.value++;
        } else {
          acc.push({ name: fundingSource, value: 1 });
        }
      });
    }
    return acc;
  }, []).sort((a, b) => b.value - a.value);

  // Calculate SDG impact data (supporting multiple SDGs per project)
  const sdgImpactData = filteredProjects.reduce((acc: any[], project) => {
    if (project.sdg_goals && project.sdg_goals.length > 0) {
      project.sdg_goals.forEach((sdg: { sdg_goal?: string; name?: string }) => {
        const sdgName = 'SDG ' + sdg.sdg_goal;
        const existingSdg = acc.find(s => s.name === sdgName);
        if (existingSdg) {
          existingSdg.count++;
        } else {
          acc.push({
            name: sdgName,
            count: 1,
            description: `${sdg.name || 'Unknown SDG'}`
          });
        }
      });
    }
    return acc;
  }, []).sort((a, b) => b.count - a.count);

  // Fetch projects from API with sessionStorage caching
  useEffect(() => {
    async function fetchProjects() {
      try {
        setLoading(true);
        
        // Check if we have cached data in sessionStorage
        const cachedData = sessionStorage.getItem('projectsData');
        
        if (cachedData) {
          // Use cached data if available
          const parsedData = JSON.parse(cachedData);
          setProjects(parsedData);
          console.log('Projects loaded from cache:', parsedData.length);
          setLoading(false);
          return;
        }
        
        // If no cached data, fetch from API
        const response = await fetch('/api/projects');
        
        if (!response.ok) {
          throw new Error(`API responded with status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Store in sessionStorage for future use
        sessionStorage.setItem('projectsData', JSON.stringify(data));
        
        setProjects(data);
        console.log('Projects loaded from API:', data.length);
      } catch (error) {
        console.error('Error fetching projects:', error);
        setError('Failed to load projects. Please try again later.');
      } finally {
        setLoading(false);
      }
    }
    
    fetchProjects();
  }, []);

  // Handler for tool filtering
  const handleToolFilter = (toolName: string | null) => {
    setSelectedTool(toolName);
  };

  // Handler for funding source filtering
  const handleFundingFilter = (fundingSource: string | null) => {
    setSelectedFunding(fundingSource);
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen">
      <ImprovedLoadingScreen message="Loading UNOPS Remote Sensing Dashboard..." />
    </div>;
  }
  
  if (error) {
    return <div className="flex items-center justify-center h-screen text-red-500">{error}</div>;
  }



  return (
    <div className="flex min-h-screen w-full flex-col bg-slate-50 font-sans">
      <div className="flex flex-col">
        <header className="sticky top-0 z-10 flex h-16 items-center gap-4 border-b bg-white px-6 shadow-sm">
          <div className="flex items-center gap-4">
            <img src="/images/unops-logo.png" alt="UNOPS Logo" className="h-8" />
            <h1 className="text-xl font-semibold">Remote Sensing Project Dashboard</h1>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <p className="text-sm text-slate-500"> MIT GenAI Lab | Beta Version | Last updated: {new Date().toLocaleDateString()}</p>
            {/* <Button variant="outline" size="sm" className="flex items-center gap-1">
              <Download className="h-4 w-4" />
              Export
            </Button> */}
          </div>
        </header>
        <main className="flex flex-1 flex-col gap-6 p-6 md:gap-8 md:p-8">
          {/* Filters Card */}
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-slate-800">Filters</CardTitle>
                <Filter className="h-4 w-4 text-slate-400" />
              </div>
              <CardDescription>Filter projects by region</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="region" className="text-sm font-medium text-slate-700">
                    Region
                  </Label>
                  <Select value={selectedRegion} onValueChange={(value) => setSelectedRegion(value)}>
                    <SelectTrigger id="region" className="bg-white border-slate-200">
                      <SelectValue placeholder="Select region" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="All">All Regions</SelectItem>
                      {regions
                        .filter(region => region !== "All")
                        .sort((a, b) => a.localeCompare(b))
                        .map((region) => (
                        <SelectItem key={region} value={region}>
                          {region}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="fundingSource" className="text-sm font-medium text-slate-700">
                    Funding Source
                  </Label>
                  <Select 
                    value={selectedFunding || "All"} 
                    onValueChange={(value) => handleFundingFilter(value === "All" ? null : value)}
                  >
                    <SelectTrigger id="fundingSource" className="bg-white border-slate-200">
                      <SelectValue placeholder="Select funding source" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="All">All Funding Sources</SelectItem>
                      {Array.from(new Set(projects.filter(p => p.donor).map(p => p.donor!)))
                        .sort((a, b) => a.localeCompare(b))
                        .map((source) => (
                          <SelectItem key={source} value={source}>
                            {source}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="mt-4 text-sm text-slate-500">
                Showing {filteredProjects.length} of {projects.length} projects
              </div>
            </CardContent>
          </Card>

          {/* SDG Impact Graph */}
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <CardTitle className="text-slate-800">Predicted SDG Impact</CardTitle>
                <a 
                  href="https://sdgs.un.org/goals" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="text-slate-500 hover:text-slate-700 transition-colors"
                  title="SDG Indicators Documentation"
                >
                  <Info className="h-4 w-4" />
                </a>
              </div>
              <CardDescription>Broader sustainable development goals impacted by project outcomes</CardDescription>
            </CardHeader>
            <CardContent>
              <SdgImpactGraph sdgImpactData={sdgImpactData} />
            </CardContent>
          </Card>

          {/* Remote Sensing Tools and Funding Source in a grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Remote Sensing Tools */}
            <Card className="shadow-sm border-slate-200">
              <CardHeader className="pb-2">
                <CardTitle className="text-slate-800">Proposed Remote Sensing Tools</CardTitle>
                <CardDescription>Number of relevant remote sensing tools for projects</CardDescription>
              </CardHeader>
              <CardContent>
                <RemoteSensingTools 
                  toolCounts={toolCounts} 
                  onToolFilter={handleToolFilter} 
                />
              </CardContent>
            </Card>

            {/* Funding Source Bar */}
            <Card className="shadow-sm border-slate-200">
              <CardHeader className="pb-2">
                <CardTitle className="text-slate-800">Funding Source</CardTitle>
                <CardDescription>Number of relevant remote sensing tools by funding source (top 20)</CardDescription>
              </CardHeader>
              <CardContent>
                <FundingSourceBar 
                  data={fundingSourceData} 
                  onFundingFilter={handleFundingFilter}
                />
              </CardContent>
            </Card>
          </div>

          <Card className="shadow-sm border-slate-200">
            <CardHeader className="pb-2">
              <CardTitle className="text-slate-800">Project Explorer</CardTitle>
              <CardDescription>Detailed information about each project</CardDescription>
            </CardHeader>
            <CardContent>
              <ProjectExplorer
                projects={filteredProjects}
                searchTerm={searchTerm}
                setSearchTerm={setSearchTerm}
                setReportProject={setReportProject}
              />
              {reportProject && (
                <ProjectReportModal
                  project={reportProject}
                  onClose={() => setReportProject(null)}
                />
              )}
            </CardContent>
          </Card>
        </main>
        <footer className="border-t bg-white p-4 text-center text-sm text-slate-500">
          UNOPS Remote Sensing Project Dashboard © {new Date().getFullYear()} | United Nations Office for Project
          Services
        </footer>
      </div>
    </div>
  )
}
