"use client";

import React, { useRef } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { FileDown } from "lucide-react";

interface ProjectReportModalProps {
  project: any;
  onClose: () => void;
}

export function ProjectReportModal({ project, onClose }: ProjectReportModalProps) {
  const contentRef = useRef<HTMLDivElement>(null);

  if (!project) return null;

  const exportToPDF = async () => {
    if (!contentRef.current) return;
    
    // Dynamically import html2pdf to avoid SSR issues
    const html2pdf = (await import('html2pdf.js')).default;
    
    const opt = {
      margin: 0.75,
      filename: `${project.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_report.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { 
        scale: 2,
        letterRendering: true,
        useCORS: true
      },
      jsPDF: { 
        unit: 'in', 
        format: 'letter', 
        orientation: 'portrait',
        compress: true,
        lineHeight: 1.5,
        hotfixes: ['px_scaling']
      },
      pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
    };

    html2pdf().set(opt).from(contentRef.current).save();
  };

  return (
    <Dialog open={!!project} onOpenChange={onClose}>
      <DialogContent className="max-w-[800px] p-6">
        <div className="flex flex-col overflow-y-auto max-h-[400px]">
          <DialogHeader className="mb-4">
            <DialogTitle>Project Report: {project.name}</DialogTitle>
          </DialogHeader>
          <div className="overflow-y-auto max-h-[400px] pr-2">
            <div ref={contentRef} className="flex-1 pdf-content">
              <style>
                {`
                  @media print {
                    .pdf-content {
                      font-size: 12pt;
                      line-height: 1.5;
                      word-wrap: break-word;
                      overflow-wrap: break-word;
                    }
                    .pdf-content strong {
                      font-weight: 600;
                    }
                    .pdf-content ul {
                      margin-top: 0.5rem;
                    }
                    .pdf-content ul li {
                      margin-bottom: 0.5rem;
                      page-break-inside: avoid;
                    }
                    .pdf-content div {
                      margin-bottom: 0.75rem;
                      page-break-inside: avoid;
                    }
                  }
                `}
              </style>
              <div className="space-y-4">
                <div className="font-bold text-xl mb-4">{project.name}</div>
                
                <div className="mb-3">
                  <strong className="text-gray-700">Project Manager:</strong> <span className="text-gray-800">{project.projectManager || "Not identified"}</span>
                  {project.projectManagerEmail && (
                    <span>
                      {" "}
                      (
                      <a href={`mailto:${project.projectManagerEmail}`} className="text-blue-600 hover:underline">
                        {project.projectManagerEmail}
                      </a>
                      )
                    </span>
                  )}
                </div>
                
                <div className="mb-3">
                  <strong className="text-gray-700">Engagement ID:</strong> <span className="text-gray-800 whitespace-normal">{project.id || "No engagement ID available"}</span>
                </div>

                <div className="mb-3">
                  <strong className="text-gray-700">Hub:</strong> <span className="text-gray-800 whitespace-normal">{project.hub || "No engagement ID available"}</span>
                </div>

                <div className="mb-3">
                  <strong className="text-gray-700">Summary:</strong> <span className="text-gray-800 whitespace-normal">{project.summary || "No summary available"}</span>
                </div>
                
                <div className="mb-3">
                  <strong className="text-gray-700">Objectives:</strong> <span className="text-gray-800 whitespace-normal">{project.objectives || "Not identified"}</span>
                </div>
                
                <div className="mb-3">
                  <strong className="text-gray-700">Problems Addressed:</strong> <span className="text-gray-800 whitespace-normal">{project.problems_addressed || "Not identified"}</span>
                </div>
                
                <div className="mb-3">
                  <strong className="text-gray-700">Beneficiaries:</strong> <span className="text-gray-800 whitespace-normal">{project.beneficiaries || "Not identified"}</span>
                </div>
                
                <div className="mb-3">
                  <strong className="text-gray-700">Anticipated Outcomes:</strong> <span className="text-gray-800 whitespace-normal">{project.anticipated_outcomes || "Not identified"}</span>
                </div>
                
                <div className="mb-3">
                  <strong className="text-gray-700">Region:</strong> <span className="text-gray-800">{project.region || "Unknown"}</span>
                </div>
                
                <div className="mb-3">
                  <strong className="text-gray-700">Funding Source:</strong> <span className="text-gray-800">{project.donor || project.fundingSource || "Unknown"}</span>
                </div>
                
                <div className="mb-3">
                  <strong className="text-gray-700">SDG Goals:</strong>
                  <ul className="list-disc ml-6 mt-2">
                    {Array.isArray(project.sdg_goals) && project.sdg_goals.length > 0 ? (
                      project.sdg_goals.map((sdg: any, idx: number) => (
                        <li key={idx} className="mb-1 break-words">
                          <span className="font-medium">SDG #{sdg.sdg_goal}:</span> {sdg.name} 
                          <div className="ml-4 text-gray-700">Relevance: {sdg.relevance}</div>
                        </li>
                      ))
                    ) : (
                      <li>No SDG goals identified</li>
                    )}
                  </ul>
                </div>
                
                <div className="mb-3">
                  <strong className="text-gray-700">SDG Indicators:</strong>
                  <ul className="list-disc ml-6 mt-2">
                    {Array.isArray(project.sdg_indicators) && project.sdg_indicators.length > 0 ? (
                      project.sdg_indicators.map((indicator: any, idx: number) => (
                        <li key={idx} className="mb-1 break-words">
                          <span className="font-medium">{indicator.sdg_indicator}:</span> {indicator.description}
                          <div className="ml-4 text-gray-700">Measurability: {indicator.measurability}</div>
                        </li>
                      ))
                    ) : (
                      <li>No SDG indicators identified</li>
                    )}
                  </ul>
                </div>
                
                <div className="mb-3">
                  <strong className="text-gray-700">Relevant Tools:</strong>
                  <ul className="list-disc ml-6 mt-2">
                    {Array.isArray(project.relevantTools) && project.relevantTools.length > 0 ? (
                      project.relevantTools.map((tool: any, idx: number) => (
                        <li key={idx} className="mb-1 break-words">
                          <span className="font-medium">{tool.name}:</span>
                          <div className="ml-4 text-gray-700">Why this is a good fit: {tool.rationale}</div>
                          {tool.project_description_context && (
                            <div className="ml-4 text-gray-700">Context: {tool.project_description_context}</div>
                          )}
                        </li>
                      ))
                    ) : (
                      <li>No relevant tools identified</li>
                    )}
                  </ul>
                </div>

          <div className="mb-3">
  <strong className="text-gray-700">URLs:</strong>
  {project.file_url && project.file_url.length > 0 ? (
    <ul className="text-gray-800 whitespace-normal list-disc pl-4">
      {project.file_url.map((file: { File_URL: string; File_Name?: string }, index: number) => (
        <li key={index}>
          <a
            href={file.File_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 underline"
          >
            {file.File_Name || "Unnamed File"}
          </a>
        </li>
      ))}
    </ul>
  ) : (
    <span className="text-gray-500">No file URLs available.</span>
  )}
</div>

              </div>
            </div>
          </div>
          <DialogFooter className="mt-6">
            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose}>
                Close
              </Button>
              <Button 
                variant="default" 
                onClick={exportToPDF}
                className="flex items-center gap-2"
              >
                <FileDown className="h-4 w-4" />
                Export PDF
              </Button>
              
            </div>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
}