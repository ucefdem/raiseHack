"use client";

import { Text } from "@react-three/drei";
import type { AgentWorkSurface } from "@raisehack/shared";

const SURFACE_LABEL: Record<Exclude<AgentWorkSurface, "none">, string> = {
  browser: "Browser",
  ide: "Coding…",
  jira: "Jira",
  terminal: "> deploy",
};

const SURFACE_COLOR: Record<Exclude<AgentWorkSurface, "none">, string> = {
  browser: "#1e293b",
  ide: "#0f172a",
  jira: "#1d4ed8",
  terminal: "#052e16",
};

interface AgentWorkSurfacePropProps {
  surface: AgentWorkSurface;
  accent: string;
}

export function AgentWorkSurfaceProp({ surface, accent }: AgentWorkSurfacePropProps) {
  if (surface === "none") return null;

  const label = SURFACE_LABEL[surface];
  const bg = SURFACE_COLOR[surface];

  return (
    <group position={[0.22, 0.32, 0.08]} rotation={[0, -0.35, 0]}>
      <mesh>
        <boxGeometry args={[0.28, 0.18, 0.02]} />
        <meshStandardMaterial color={bg} roughness={0.4} metalness={0.1} />
      </mesh>
      <mesh position={[0, 0.07, 0.012]}>
        <boxGeometry args={[0.28, 0.03, 0.01]} />
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.3} />
      </mesh>
      <Text
        position={[0, -0.01, 0.012]}
        fontSize={0.035}
        color={surface === "terminal" ? "#4ade80" : "#e2e8f0"}
        anchorX="center"
        anchorY="middle"
        maxWidth={0.24}
      >
        {label}
      </Text>
    </group>
  );
}

interface AgentErrorSignalProps {
  severity: "warning" | "critical";
}

export function AgentErrorSignal({ severity }: AgentErrorSignalProps) {
  const color = severity === "critical" ? "#ef4444" : "#f59e0b";

  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.015, 0]}>
        <ringGeometry args={[0.32, 0.38, 32]} />
        <meshBasicMaterial color={color} transparent opacity={0.75} />
      </mesh>
      <mesh position={[0, 0.62, 0]}>
        <sphereGeometry args={[0.05, 12, 12]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.9}
        />
      </mesh>
      <Text
        position={[0, 0.62, 0.052]}
        fontSize={0.06}
        color="#fff"
        anchorX="center"
        anchorY="middle"
      >
        !
      </Text>
    </group>
  );
}
