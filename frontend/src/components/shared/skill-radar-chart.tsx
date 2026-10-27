"use client";

import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export interface RadarDimension {
  dimension: string;
  score: number;
}

export function SkillRadarChart({ data }: { data: RadarDimension[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Skill Radar</CardTitle>
        <CardDescription>Score breakdown across evaluation dimensions.</CardDescription>
      </CardHeader>
      <CardContent className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} outerRadius="75%">
            <PolarGrid stroke="#E2E8F0" />
            <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 12, fill: "#475569" }} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10, fill: "#94A3B8" }} />
            <Radar dataKey="score" stroke="#059669" fill="#059669" fillOpacity={0.25} strokeWidth={2} />
          </RadarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
