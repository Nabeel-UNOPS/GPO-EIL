"use client"

import React, { useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts";
import { Card, CardContent } from "@/components/ui/card";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { BarChart2, PieChart as PieChartIcon, Info } from "lucide-react";
import { sdgColors as sdgColorsArray } from "@/lib/sdg-colors";

interface SdgImpactGraphProps {
  sdgImpactData: any[]
}

// Custom tick component for rotated X-axis labels
const CustomXAxisTick = (props: any) => {
  const { x, y, payload, data } = props;
  const sdgName = payload.value;
  
  // Find the corresponding entry in the data to get the description
  const entry = data?.find((item: any) => item.name === sdgName);
  let description = entry?.description || '';
  
  // Break the description into two parts if "and" is present
  let firstPart = description;
  let secondPart = '';
  
  if (description.includes(' and ')) {
    const parts = description.split(' and ');
    firstPart = parts[0] + ' & ' ;
    secondPart = parts.slice(1).join(' and ');
  }
  
  return (
    <g transform={`translate(${x},${y})`}>
      <text 
        x={0} 
        y={0} 
        dy={16} 
        textAnchor="end" 
        fill="#666" 
        fontSize="10px"
        transform="rotate(-30)"
      >
        {sdgName}
      </text>
      {firstPart && (
        <text 
          x={10} 
          y={0} 
          dy={28} 
          textAnchor="end" 
          fill="#666" 
          fontSize="9px"
          transform="rotate(-30)"
        >
          {firstPart}
        </text>
      )}
      {secondPart && (
        <text 
          x={10} 
          y={0} 
          dy={40} 
          textAnchor="end" 
          fill="#666" 
          fontSize="9px"
          transform="rotate(-30)"
        >
          {secondPart}
        </text>
      )}
    </g>
  );
};

export function SdgImpactGraph({ sdgImpactData }: SdgImpactGraphProps) {
  const [chartType, setChartType] = useState<"bar" | "pie">("bar");
  
  // Filter out "SDG N/A" entries
  const filteredData = sdgImpactData.filter(item => item.name !== "SDG N/A");
  
  // SDG colors from the official palette
  const sdgColors: { [key: string]: string } = {
    "SDG 1": "#E5243B",   // Red
    "SDG 2": "#DDA63A",   // Mustard
    "SDG 3": "#4C9F38",   // Kelly Green
    "SDG 4": "#C5192D",   // Dark Red
    "SDG 5": "#FF3A21",   // Red Orange
    "SDG 6": "#26BDE2",   // Bright Blue
    "SDG 7": "#FCC30B",   // Yellow
    "SDG 8": "#A21942",   // Burgundy Red
    "SDG 9": "#FD6925",   // Orange
    "SDG 10": "#DD1367",  // Magenta
    "SDG 11": "#FD9D24",  // Golden Yellow
    "SDG 12": "#BF8B2E",  // Dark Mustard
    "SDG 13": "#3F7E44",  // Dark Green
    "SDG 14": "#0A97D9",  // Blue
    "SDG 15": "#56C02B",  // Lime Green
    "SDG 16": "#00689D",  // Royal Blue
    "SDG 17": "#19486A",  // Navy Blue
  };

  // Group data for the outer ring (detailed breakdown)
  const outerRingData = [...filteredData];

  // Group data for the inner ring (simplified view)
  // You can customize this grouping logic as needed
  const innerRingData = filteredData.reduce((acc: any[], item) => {
    // Example: Group by SDG category (you can define your own grouping logic)
    const category = item.name.split(' ')[0]; // Just an example - gets "SDG"
    const existingCategory = acc.find(c => c.category === category);
    
    if (existingCategory) {
      existingCategory.value += item.count;
    } else {
      acc.push({ 
        name: category, 
        value: item.count,
        category: category
      });
    }
    return acc;
  }, []);

  // Sort data in descending order for bar chart
  const sortedData = [...filteredData].sort((a, b) => b.count - a.count);

  return (
    <div className="w-full">
      <div className="flex justify-center mb-4 items-center gap-4">
        <ToggleGroup type="single" value={chartType} onValueChange={(value) => setChartType(value as "bar" | "pie")}>
          <ToggleGroupItem value="bar" aria-label="Bar Chart" title="Bar Chart">
            <BarChart2 className="h-4 w-4" />
          </ToggleGroupItem>
          <ToggleGroupItem value="pie" aria-label="Pie Chart" title="Pie Chart">
            <PieChartIcon className="h-4 w-4" />
          </ToggleGroupItem>
        </ToggleGroup>
      </div>

      <ResponsiveContainer width="100%" height={500}>
        {chartType === "pie" ? (
          <PieChart>
            {/* Inner pie */}
            <Pie
              data={innerRingData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={80}
              fill="#FFFFFF"
              labelLine={false}
              label={true}
            >
              {innerRingData.map((entry, index) => (
                <Cell 
                  key={`cell-inner-${index}`} 
                  fill={"#FFFFFF"} 
                  stroke="#FFFFFF"
                />
              ))}
            </Pie>

            {/* Center Label for Inner Ring */}
            <text
              x="50%"
              y="50%"
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="24px"
              fontWeight="bold"
              fill="#000000"
              pointerEvents="none"
            >
              SDG
            </text>
            
            {/* Outer pie */}
            <Pie
              data={outerRingData}
              dataKey="count"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={80}
              outerRadius={180}
              labelLine={false}
              label={({ name, cx, cy, midAngle, innerRadius, outerRadius, count }) => {
                const RADIAN = Math.PI / 180;
                // Position in the middle of the slice
                const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
                const x = cx + radius * Math.cos(-midAngle * RADIAN);
                const y = cy + radius * Math.sin(-midAngle * RADIAN);
                
                // For very small slices, don't show label to avoid overlap
                if (count < 8) return null;
                
                return (
                  <text 
                    x={x} 
                    y={y} 
                    fill="white"
                    textAnchor="middle"
                    dominantBaseline="central"
                    style={{ fontWeight: 'bold', fontSize: '8px'}}
                  >
                    {`${name}`}
                  </text>
                );
              }}
            >
              {outerRingData.map((entry, index) => (
                <Cell 
                  key={`cell-outer-${index}`} 
                  fill={sdgColors[entry.name] || "#b3b3b3"} 
                />
              ))}
            </Pie>
            
            <Tooltip
              formatter={(value, name, props) => {
                return [`Number of Projects Contributing to ${name}: ${value}`];
              }}
              contentStyle={{
                backgroundColor: "white",
                border: "1px solid #e2e8f0",
                borderRadius: "4px",
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
              }}
            />
          </PieChart>
        ) : (
          <BarChart data={sortedData} margin={{ top: 10, right: 30, left: 30, bottom: 30 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={true} horizontal={true} />
            <XAxis
              type="category"
              dataKey="name"
              height={120}
              tick={(props) => <CustomXAxisTick {...props} data={sortedData} />}
              stroke="#64748b"
              axisLine={{ stroke: "#e2e8f0" }}
            />
            <YAxis
              type="number"
              tick={{ fontSize: 10 }}
              stroke="#64748b"
              tickLine={false}
              axisLine={{ stroke: "#e2e8f0" }}
            />
            <Tooltip
              formatter={(value, name) => [`${value}`, `Number of Projects`]}
              contentStyle={{
                backgroundColor: "white",
                border: "1px solid #e2e8f0",
                borderRadius: "4px",
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
              }}
            />
            <Bar 
              dataKey="count" 
              name="Projects"
              radius={[4, 4, 0, 0]}
            >
              {sortedData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={sdgColors[entry.name] || "#b3b3b3"} 
                />
              ))}
            </Bar>
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}