"use client"

import { useState, useEffect, useCallback, memo, useRef, useMemo } from "react"
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, Cell } from "recharts"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface RemoteSensingToolsProps {
  toolCounts: any[]
  onToolFilter?: (toolName: string | null) => void
}

// Custom tick component for X-axis labels to break text into multiple lines
const CustomXAxisTick = memo((props: any) => {
  const { x, y, payload } = props;
  const value = payload.value;
  const words = value.split(' ');
  
  // Add a vertical offset to position labels lower than the axis line
  const verticalOffset = 10;
  
  if (words.length <= 2) {
    return (
      <g transform={`translate(${x},${y + verticalOffset})`}>
        <text x={0} y={0} dy={16} textAnchor="middle" fill="#666" fontSize={10}>
          {value}
        </text>
      </g>
    );
  }
  
  // For longer phrases, break into multiple lines
  const firstLine = words.slice(0, Math.ceil(words.length / 2)).join(' ');
  const secondLine = words.slice(Math.ceil(words.length / 2)).join(' ');
  
  return (
    <g transform={`translate(${x},${y + verticalOffset})`}>
      <text x={0} y={0} textAnchor="middle" fill="#666" fontSize={10}>
        <tspan x={0} dy="0">{firstLine}</tspan>
        <tspan x={0} dy="12">{secondLine}</tspan>
      </text>
    </g>
  );
});

// Custom tooltip content component
const CustomTooltip = memo(({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <Card className="border shadow-sm">
        <CardContent className="p-3">
          <div className="text-sm font-medium">{data.name}</div>
          <div className="text-xs text-slate-500 mt-1">
            Proposed for <span className="font-semibold text-slate-700">{data.count}</span> projects
          </div>
          <div className="text-xs text-slate-600 mt-2 border-t pt-2">{data.description}</div>
        </CardContent>
      </Card>
    );
  }
  return null;
});

export function RemoteSensingTools({ toolCounts, onToolFilter }: RemoteSensingToolsProps) {
  // Add state to track selected tool
  const [selectedTool, setSelectedTool] = useState<string | null>(null)
  const chartRef = useRef<any>(null)
  
  // Store the original order of tools when component first renders
  const originalToolOrder = useRef<string[]>([]);
  
  // On first render, store the original order of tools
  useEffect(() => {
    if (toolCounts.length > 0 && originalToolOrder.current.length === 0) {
      originalToolOrder.current = toolCounts.map(tool => tool.name);
      console.log("ORIGINAL TOOL ORDER:", originalToolOrder.current);
    }
  }, [toolCounts]);
  
  // Reorder the tools to maintain original order regardless of count changes
  const orderedTools = useMemo(() => {
    if (originalToolOrder.current.length === 0) {
      return toolCounts; // Return as-is for the first render
    }
    
    // Create a mapping of tools by name for easy lookup
    const toolsMap = toolCounts.reduce((acc, tool) => {
      acc[tool.name] = tool;
      return acc;
    }, {} as Record<string, any>);
    
    // Create a new array with tools in the original order, but with updated counts
    const reorderedTools = originalToolOrder.current
      .filter(name => toolsMap[name]) // Only include tools that exist in the current toolCounts
      .map(name => toolsMap[name]); // Get the current tool data with updated count
    
    console.log("MAINTAINING ORIGINAL ORDER:", reorderedTools.map(t => t.name));
    return reorderedTools;
  }, [toolCounts]);
  
  // Add effect to log when selected tool changes
  useEffect(() => {
    console.log("SELECTION CHANGED - Current selected tool:", selectedTool);
  }, [selectedTool]);

  // Tools are already sorted by count in descending order from the mock data

  // Use a bright blue color for all bars
  const barColor = "#B4B4B4" 
  // Use a more distinct color for selected bar
  const selectedBarColor = "#4F46E5" // Indigo color for better visibility
  
  // Create a direct click handler for each bar using its index
  const handleDirectBarClick = useCallback((toolName: string) => {
    console.log("DIRECT BAR CLICK:", toolName);
    
    // If clicking the already selected tool, clear the filter
    if (selectedTool === toolName) {
      console.log("CLEARING SELECTION - Was:", selectedTool);
      setSelectedTool(null)
      if (onToolFilter) onToolFilter(null)
    } else {
      console.log("SELECTING NEW TOOL - New:", toolName, "Previous:", selectedTool);
      
      // Always reset the filter first
      setSelectedTool(null)
      if (onToolFilter) onToolFilter(null)
      
      // Then set the new selection after a small delay
      setTimeout(() => {
        console.log("APPLYING NEW SELECTION:", toolName);
        setSelectedTool(toolName)
        if (onToolFilter) onToolFilter(toolName)
      }, 50)
    }
  }, [selectedTool, onToolFilter]);
  
  // Reset filter function
  const resetFilter = useCallback(() => {
    console.log("FILTER RESET - Was:", selectedTool);
    setSelectedTool(null)
    if (onToolFilter) onToolFilter(null)
  }, [onToolFilter, selectedTool]);

  // Function to determine cell fill color - memoized for performance
  const getCellFillColor = useCallback((entryName: string) => {
    const isSelected = entryName === selectedTool;
    const color = isSelected ? selectedBarColor : barColor;
    
    // Log color only when rendering (not on every state change)
    if (isSelected) {
      console.log("COLOR APPLIED - Tool:", entryName, "Color:", color);
    }
    
    return color;
  }, [selectedTool, selectedBarColor, barColor]);

  // Log all tools on initial render to verify what's available
  useEffect(() => {
    console.log("ALL TOOLS:", toolCounts.map(tool => tool.name));
  }, [toolCounts]);

  return (
    <div className="w-full">
      {selectedTool && (
        <div className="mb-4 flex items-center">
          <div className="text-sm text-slate-600 flex-1">
            Showing projects that use <span className="font-semibold">{selectedTool}</span>
          </div>
          <button 
            onClick={resetFilter}
            className="text-xs text-slate-500 hover:text-slate-800 px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded-md transition-colors"
          >
            Clear filter
          </button>
        </div>
      )}
      
      {/* Custom bar chart implementation */}
      <div className="w-full" style={{ height: '500px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart 
            ref={chartRef}
            data={orderedTools} 
            margin={{ top: 10, right: 30, left: 10, bottom: 0 }}
          >
            <XAxis 
              type="category" 
              dataKey="name" 
              stroke="#64748b"
              tick={<CustomXAxisTick />}
              tickLine={false}
              axisLine={{ stroke: "#e2e8f0" }}            
              height={60}
              interval={0}
            />
            <YAxis
              type="number"
              stroke="#64748b"
              tick={{ fontSize: 10 }}
              tickLine={false}
              axisLine={{ stroke: "#e2e8f0" }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar 
              dataKey="count" 
              radius={[4, 4, 0, 0]}
              barSize={50}
              label={{
                position: 'top',
                formatter: (value: number) => `${value}`,
                fill: '#64748b',
                fontSize: 10,
                fontWeight: 400,
                offset: 10
              }}
              // Remove the onClick from Bar component
            >
              {orderedTools.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={getCellFillColor(entry.name)}
                  // Add direct click handler to each Cell
                  onClick={() => handleDirectBarClick(entry.name)}
                  cursor="pointer"
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
