"use client"

import React, { useState, useCallback, memo, useRef, useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Card, CardContent } from "@/components/ui/card";

// Update interface to include the onFundingFilter callback
interface FundingSourceChartProps {
  data: { name: string; value: number }[];
  onFundingFilter?: (fundingSource: string | null) => void;
}

// Custom tooltip component
const CustomTooltip = memo(({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <Card className="border shadow-sm">
        <CardContent className="p-3">
          <div className="text-sm font-medium">{data.name}</div>
          <div className="text-xs text-slate-500 mt-1">
            <span className="font-semibold text-slate-700">{data.value}</span> tools applicable
          </div>
        </CardContent>
      </Card>
    );
  }
  return null;
});

export function FundingSourceBar({ data, onFundingFilter }: FundingSourceChartProps) {
  // Add state to track selected funding source
  const [selectedFunding, setSelectedFunding] = useState<string | null>(null);
  const chartRef = useRef<any>(null);
  
  // Store the original order of funding sources when component first renders
  const originalFundingOrder = useRef<string[]>([]);
  
  // On first render, store the original order of funding sources
  useMemo(() => {
    if (data.length > 0 && originalFundingOrder.current.length === 0) {
      originalFundingOrder.current = data.map(source => source.name);
      console.log("ORIGINAL FUNDING ORDER:", originalFundingOrder.current);
    }
  }, [data]);
  
  // Reorder the funding sources to maintain original order regardless of value changes
  // and limit to top 20 funding sources
  const orderedData = useMemo(() => {
    if (originalFundingOrder.current.length === 0) {
      // Return top 20 sorted data for first render
      return [...data].sort((a, b) => b.value - a.value).slice(0, 20);
    }
    
    // Create a mapping of funding sources by name for easy lookup
    const sourcesMap = data.reduce((acc, source) => {
      acc[source.name] = source;
      return acc;
    }, {} as Record<string, any>);
    
    // Create a new array with funding sources in the original order, but with updated values
    let reorderedSources = originalFundingOrder.current
      .filter(name => sourcesMap[name]) // Only include sources that exist in the current data
      .map(name => sourcesMap[name]); // Get the current funding source data with updated value
    
    // Limit to top 20 funding sources based on value
    reorderedSources = reorderedSources
      .sort((a, b) => b.value - a.value)
      .slice(0, 20);
    
    console.log("MAINTAINING ORIGINAL FUNDING ORDER (TOP 12):", reorderedSources.map(s => s.name));
    return reorderedSources;
  }, [data]);

  // Add effect to log when selected funding source changes
  useMemo(() => {
    console.log("SELECTION CHANGED - Current selected funding source:", selectedFunding);
  }, [selectedFunding]);

  // Bar colors
  const barColor = "#009edb" 
  const selectedBarColor = "#008edb" 
  
  // Create a direct click handler for each bar
  const handleBarClick = useCallback((fundingSource: string) => {
    console.log("DIRECT BAR CLICK:", fundingSource);
    
    // If clicking the already selected funding source, clear the filter
    if (selectedFunding === fundingSource) {
      console.log("CLEARING SELECTION - Was:", selectedFunding);
      setSelectedFunding(null)
      if (onFundingFilter) onFundingFilter(null)
    } else {
      console.log("SELECTING NEW FUNDING SOURCE - New:", fundingSource, "Previous:", selectedFunding);
      
      // Always reset the filter first
      setSelectedFunding(null)
      if (onFundingFilter) onFundingFilter(null)
      
      // Then set the new selection after a small delay
      setTimeout(() => {
        console.log("APPLYING NEW SELECTION:", fundingSource);
        setSelectedFunding(fundingSource)
        if (onFundingFilter) onFundingFilter(fundingSource)
      }, 50)
    }
  }, [selectedFunding, onFundingFilter]);
  
  // Reset filter function
  const resetFilter = useCallback(() => {
    console.log("FILTER RESET - Was:", selectedFunding);
    setSelectedFunding(null)
    if (onFundingFilter) onFundingFilter(null)
  }, [onFundingFilter, selectedFunding]);

  // Function to determine cell fill color
  const getCellFillColor = useCallback((entryName: string) => {
    return entryName === selectedFunding ? selectedBarColor : barColor;
  }, [selectedFunding, selectedBarColor, barColor]);
  
  return (
    <div className="w-full">
      {selectedFunding && (
        <div className="mb-4 flex items-center">
          <div className="text-sm text-slate-600 flex-1">
            Showing projects funded by <span className="font-semibold">{selectedFunding}</span>
          </div>
          <button 
            onClick={resetFilter}
            className="text-xs text-slate-500 hover:text-slate-800 px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded-md transition-colors"
          >
            Clear filter
          </button>
        </div>
      )}
      
      {data && data.length > 0 ? (
        <ResponsiveContainer width="100%" height={500}>
          <BarChart 
            ref={chartRef}
            data={orderedData}
            width={600}
            height={400}
            barGap={2}
            barCategoryGap={2}
            layout="vertical"
            margin={{ top: 10, right: 30, left: -130, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
            <XAxis 
              type="number"
              stroke="#64748b"
              tick={{ fontSize: 10 }}
              axisLine={{ stroke: "#e2e8f0" }}
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 8 }}
              width={300}
              stroke="#64748b"
              tickLine={false}
              axisLine={{ stroke: "#e2e8f0" }}
              interval={0} // Show all ticks
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar 
              dataKey="value" 
              radius={[0, 4, 4, 0]}
              barSize={20}
              label={{
                position: 'right',
                formatter: (value: number) => `${value}`,
                fill: '#64748b',
                fontSize: 10,
                fontWeight: 400,
                offset: 10
              }}
            >
              {orderedData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={getCellFillColor(entry.name)}
                  onClick={() => handleBarClick(entry.name)}
                  cursor="pointer"
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex items-center justify-center h-full text-slate-500">
          No funding source data available
        </div>
      )}
    </div>
  );
}
