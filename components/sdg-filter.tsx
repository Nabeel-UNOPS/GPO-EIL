"use client"

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"

interface SdgFilterProps {
  sdgs: any[]
  selectedSdg: string
  setSelectedSdg: (sdg: string) => void
}

export function SdgFilter({ sdgs, selectedSdg, setSelectedSdg }: SdgFilterProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor="sdg" className="text-sm font-medium text-slate-700">
        Sustainable Development Goal
      </Label>
      <Select value={selectedSdg} onValueChange={setSelectedSdg}>
        <SelectTrigger id="sdg" className="bg-white border-slate-200">
          <SelectValue placeholder="Select SDG" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="All">All SDGs</SelectItem>
          {sdgs.map((sdg) => (
            <SelectItem key={sdg.name} value={sdg.name}>
              {sdg.shortName} - {sdg.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
