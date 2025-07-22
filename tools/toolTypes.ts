
export interface Tool {
    name: string;
    description: string;
    parameters: {
        type: "OBJECT";
        properties: Record<string, { type: string; description: string; }>;
        required?: string[];
    };
    execute: (params: any) => Promise<{ output: any; summary: string }>;
}

export type ToolRegistry = Map<string, Tool>;
