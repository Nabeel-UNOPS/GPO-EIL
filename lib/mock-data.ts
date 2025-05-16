// Generate mock data for the UNOPS dashboard

// Remote sensing tools with descriptions
export const remoteSensingTools = [
  {
    name: "Satellite Imagery & Geospatial Analysis",
    description: "Uses satellite data to monitor land use, environmental changes, and infrastructure development.",
  },
  {
    name: "AI-Powered Remote Sensing",
    description:
      "Applies machine learning algorithms to analyze remote sensing data for pattern recognition and predictive insights.",
  },
  {
    name: "UAV & Aerial Data Integration",
    description:
      "Utilizes drones and aerial platforms to collect high-resolution imagery and 3D data for detailed site analysis.",
  },
  {
    name: "Monitoring & Early Warning",
    description:
      "Implements sensor networks and real-time data collection systems to detect and alert about environmental or security threats.",
  },
  {
    name: "Dashboard & Decision Support",
    description:
      "Provides visualization tools and interactive interfaces to help stakeholders interpret complex geospatial data.",
  },
]

// SDG impact descriptions
const sdgImpactDescriptions = {
  "Climate Action (SDG 13)": "Projects contribute to climate change mitigation, adaptation, and resilience building.",
  "Life on Land (SDG 15)": "Projects help protect, restore, and promote sustainable use of terrestrial ecosystems.",
  "Clean Water and Sanitation (SDG 6)":
    "Projects improve water quality, efficiency, and access to sanitation services.",
  "Sustainable Cities (SDG 11)":
    "Projects enhance urban planning, reduce environmental impacts, and build resilient communities.",
  "Zero Hunger (SDG 2)": "Projects address food security, improve nutrition, and promote sustainable agriculture.",
}

// Function to generate rationales for why a tool is a good fit for a project
function generateToolRationale(projectName: string, sdg: string, tool: string): string {
  const rationales = {
    "Satellite Imagery & Geospatial Analysis": [
      "This project's large geographic scope makes satellite imagery ideal for comprehensive monitoring.",
      "The environmental focus of this project would benefit from regular satellite monitoring of land use changes.",
      "Satellite imagery would provide crucial baseline data for measuring project impact over time.",
      "The remote location of this project makes satellite monitoring the most cost-effective approach.",
      "Geospatial analysis would help identify optimal locations for infrastructure development in this project.",
    ],
    "AI-Powered Remote Sensing": [
      "The complex data patterns in this project would benefit from AI-powered analysis to identify trends.",
      "Machine learning could help predict potential environmental impacts before they occur in this region.",
      "The large dataset this project will generate requires AI tools for efficient processing.",
      "AI algorithms could identify subtle changes in environmental conditions relevant to project outcomes.",
      "Pattern recognition capabilities would enhance the monitoring of project implementation progress.",
    ],
    "UAV & Aerial Data Integration": [
      "The small-scale, detailed mapping requirements make UAVs ideal for this project.",
      "Regular drone surveys would provide high-resolution imagery needed for precise monitoring.",
      "The terrain complexity in this region makes UAV data collection more practical than other methods.",
      "3D modeling from drone imagery would enhance planning and stakeholder communication.",
      "UAVs would allow for rapid assessment of changing conditions in the project area.",
    ],
    "Monitoring & Early Warning": [
      "Real-time monitoring would allow for immediate intervention if environmental conditions change.",
      "Early warning capabilities are essential given the climate vulnerability of this project area.",
      "Continuous data collection would provide valuable insights into seasonal variations affecting the project.",
      "Automated alerts would ensure timely response to potential threats to project infrastructure.",
      "Sensor networks would enable comprehensive monitoring of multiple environmental parameters.",
    ],
    "Dashboard & Decision Support": [
      "The multiple stakeholders involved would benefit from intuitive data visualization tools.",
      "Interactive dashboards would make complex project data accessible to non-technical decision-makers.",
      "Customizable reporting features would support diverse information needs across project teams.",
      "Data integration capabilities would provide a holistic view of project performance.",
      "Scenario modeling tools would support adaptive management approaches for this project.",
    ],
  }

  // Select a rationale based on project characteristics
  const options = rationales[tool as keyof typeof rationales] || []
  const index = (projectName.length + sdg.length) % options.length
  return options[index]
}


export function generateMockData() {
  // SDGs
  const sdgs = [
    { name: "No Poverty", shortName: "SDG 1" },
    { name: "Zero Hunger", shortName: "SDG 2" },
    { name: "Good Health and Well-being", shortName: "SDG 3" },
    { name: "Quality Education", shortName: "SDG 4" },
    { name: "Gender Equality", shortName: "SDG 5" },
    { name: "Clean Water and Sanitation", shortName: "SDG 6" },
    { name: "Affordable and Clean Energy", shortName: "SDG 7" },
    { name: "Decent Work and Economic Growth", shortName: "SDG 8" },
    { name: "Industry, Innovation and Infrastructure", shortName: "SDG 9" },
    { name: "Reduced Inequalities", shortName: "SDG 10" },
    { name: "Sustainable Cities and Communities", shortName: "SDG 11" },
    { name: "Responsible Consumption and Production", shortName: "SDG 12" },
    { name: "Climate Action", shortName: "SDG 13" },
    { name: "Life Below Water", shortName: "SDG 14" },
    { name: "Life on Land", shortName: "SDG 15" },
    { name: "Peace, Justice and Strong Institutions", shortName: "SDG 16" },
    { name: "Partnerships for the Goals", shortName: "SDG 17" },
  ]

  // Regions
  const regions = ["Africa", "Asia", "Europe", "Latin America and Caribbean", "Middle East", "North America", "Oceania"]

  // Funding sources
  const fundingSources = [
    "World Bank",
    "European Union",
    "USAID",
    "DFID",
    "Government of Japan",
    "Government of Sweden",
    "Government of Norway",
    "Government of Germany",
    "UNDP",
    "Private Sector",
    "Global Environment Facility",
    "Green Climate Fund",
    "Asian Development Bank",
    "African Development Bank",
    "Inter-American Development Bank",
  ]

  // Project statuses
  const statuses = ["Active", "Completed", "Planned", "On Hold"]

  // Project names
  const projectPrefixes = [
    "Sustainable",
    "Resilient",
    "Inclusive",
    "Integrated",
    "Comprehensive",
    "Community-based",
    "Rural",
    "Urban",
    "National",
    "Regional",
  ]

  const projectTypes = [
    "Infrastructure Development",
    "Healthcare System",
    "Education Program",
    "Water Management",
    "Renewable Energy",
    "Disaster Recovery",
    "Capacity Building",
    "Economic Development",
    "Environmental Conservation",
    "Food Security",
    "Gender Equality",
    "Governance Reform",
  ]

  const projectLocations = [
    "in East Africa",
    "in Southeast Asia",
    "in Central America",
    "in the Pacific Islands",
    "in the Middle East",
    "in Eastern Europe",
    "in West Africa",
    "in South Asia",
    "in the Caribbean",
    "in the Balkans",
    "in the Andean Region",
    "in the Sahel",
  ]

  // Project manager names and emails
  const projectManagers = [
    { name: "Alex Johnson", email: "alex.johnson@unops.org" },
    { name: "Maria Garcia", email: "maria.garcia@unops.org" },
    { name: "David Kim", email: "david.kim@unops.org" },
    { name: "Sarah Ahmed", email: "sarah.ahmed@unops.org" },
    { name: "James Wilson", email: "james.wilson@unops.org" },
    { name: "Priya Patel", email: "priya.patel@unops.org" },
    { name: "Carlos Rodriguez", email: "carlos.rodriguez@unops.org" },
    { name: "Emma Thompson", email: "emma.thompson@unops.org" },
    { name: "Liu Wei", email: "liu.wei@unops.org" },
    { name: "Fatima Al-Farsi", email: "fatima.alfarsi@unops.org" },
    { name: "Kwame Osei", email: "kwame.osei@unops.org" },
    { name: "Sophia Müller", email: "sophia.muller@unops.org" },
  ]

  // view here for the project formats
  // Generate random projects
  const projects = Array.from({ length: 50 }, (_, i) => {
    const id = i + 1
    // Assign a random SDG from the list
    const randomSdgIndex = Math.floor(Math.random() * sdgs.length)
    const sdg = sdgs[randomSdgIndex].name
    const sdgNumber = randomSdgIndex + 1 // Ensure we have the correct SDG number

    const region = regions[Math.floor(Math.random() * regions.length)]
    const fundingSource = fundingSources[Math.floor(Math.random() * fundingSources.length)]

    // Random project name
    const prefix = projectPrefixes[Math.floor(Math.random() * projectPrefixes.length)]
    const type = projectTypes[Math.floor(Math.random() * projectTypes.length)]
    const location = projectLocations[Math.floor(Math.random() * projectLocations.length)]
    const name = `${prefix} ${type} ${location}`
    // Project manager
    const projectManager = projectManagers[Math.floor(Math.random() * projectManagers.length)]
    // Assign relevant remote sensing tools with rationales
    const toolNames = remoteSensingTools.map((tool) => tool.name)
    const relevantTools = []

    // Determine how many tools are relevant (1-2)
    const numTools = Math.floor(Math.random() * 2) + 1

    // Create a copy of the tools array and shuffle it
    const shuffledTools = [...toolNames].sort(() => 0.5 - Math.random())

    // Take the first numTools from the shuffled array
    for (let j = 0; j < numTools; j++) {
      if (j < shuffledTools.length) {
        const toolName = shuffledTools[j]
        relevantTools.push({
          name: toolName,
          rationale: generateToolRationale(name, sdg, toolName),
        })
      }
    }

    return {
      id,
      name,
      sdg,
      sdgNumber, // Store the actual SDG number
      region,
      fundingSource,
      projectManager: projectManager.name,
      projectManagerEmail: projectManager.email,
      relevantTools,
    }
  })

  // Calculate tool usage counts
  const toolCounts = remoteSensingTools
    .map((tool) => {
      const count = projects.filter((project) => project.relevantTools.some((rt) => rt.name === tool.name)).length

      return {
        name: tool.name,
        count,
        description: tool.description,
      }
    })
    .sort((a, b) => b.count - a.count) // Sort by count in descending order

  // Generate SDG impact data with the same structure as toolCounts
  const sdgImpactData = [
    {
      name: "Climate Action (SDG 13)",
      count: 78,
      description: sdgImpactDescriptions["Climate Action (SDG 13)"],
    },
    {
      name: "Life on Land (SDG 15)",
      count: 65,
      description: sdgImpactDescriptions["Life on Land (SDG 15)"],
    },
    {
      name: "Clean Water and Sanitation (SDG 6)",
      count: 52,
      description: sdgImpactDescriptions["Clean Water and Sanitation (SDG 6)"],
    },
    {
      name: "Sustainable Cities (SDG 11)",
      count: 47,
      description: sdgImpactDescriptions["Sustainable Cities (SDG 11)"],
    },
    {
      name: "Zero Hunger (SDG 2)",
      count: 39,
      description: sdgImpactDescriptions["Zero Hunger (SDG 2)"],
    },
  ]

  return { projects, regions, fundingSources, toolCounts, sdgImpactData }
}

// !!! focus on creating this firs 
// projects are array of objects with the following structure:
// {
//   id: number,
//   name: string,
//   sdg: string,
//   sdgNumber: number,
//   region: string,
//   fundingSource: string,
//   projectManager: string,
//   projectManagerEmail: string,
//   hasSubmittedReports: boolean,
//   hasCompleteImpactData: boolean,
//   documents: boolean,
//   relevantTools: Array<{ name: string; rationale: string }>, (rs tools)
// }


// !!! This is a static table 
// regions, fundingSources are arrays of strings (all categories of regions, sdgs, funding sources)


// !!! This will need a new table or a backend calculation to get
// toolCounts is array of objects with the following structure:
// {
//   name: string,
//   count: number,
//   description: string,
// }

// sdgImpactData is array of objects with the following structure:
// {
//   name: string, (name of the sdg)
//   count: number, (number of projects that impact this sdg)
//   description: string, (what the sdg is)
// }
