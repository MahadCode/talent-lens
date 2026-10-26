"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export interface WeeklyPoint {
  day: string;
  applications: number;
  interviews: number;
}

export function WeeklyAnalyticsChart({ data }: { data: WeeklyPoint[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Weekly Analytics</CardTitle>
        <CardDescription>Applications received vs. interviews conducted.</CardDescription>
      </CardHeader>
      <CardContent className="h-64 pl-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 16, left: -16, bottom: 0 }}>
            <defs>
              <linearGradient id="applicationsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#059669" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#059669" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="interviewsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#34D399" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#34D399" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
            <XAxis dataKey="day" tick={{ fontSize: 12, fill: "#475569" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 12, fill: "#475569" }} axisLine={false} tickLine={false} width={28} />
            <Tooltip
              contentStyle={{
                borderRadius: 12,
                border: "1px solid #E2E8F0",
                fontSize: 13,
                boxShadow: "0 4px 16px -4px rgb(15 23 42 / 0.1)",
              }}
            />
            <Area type="monotone" dataKey="applications" stroke="#059669" fill="url(#applicationsGradient)" strokeWidth={2} />
            <Area type="monotone" dataKey="interviews" stroke="#34D399" fill="url(#interviewsGradient)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
