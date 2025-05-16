"use client"

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"

interface RegionFilterProps {
  regions: string[]
  selectedRegion: string
  setSelectedRegion: (region: string) => void
}

export function RegionFilter({ regions, selectedRegion, setSelectedRegion }: RegionFilterProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor="region" className="text-sm font-medium text-slate-700">
        Region
      </Label>
      <Select value={selectedRegion} onValueChange={setSelectedRegion}>
        <SelectTrigger id="region" className="bg-white border-slate-200">
          <SelectValue placeholder="Select region" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="All">All Regions</SelectItem>
          {regions.map((region) => (
            <SelectItem key={region} value={region}>
              {region}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
