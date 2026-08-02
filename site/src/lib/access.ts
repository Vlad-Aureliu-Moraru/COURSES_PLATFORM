interface ModuleEntry {
  id: string;
  data: {
    free?: boolean;
    order?: number;
    title?: string;
    est_time?: string;
    description?: string;
  };
}

export function isFree(entry: ModuleEntry): boolean {
  return Boolean(entry.data.free);
}
