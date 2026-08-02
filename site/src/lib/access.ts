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

const DEV_UNLOCK = import.meta.env.PUBLIC_DEV_UNLOCK === 'true';

export function isFree(entry: ModuleEntry): boolean {
  return Boolean(entry.data.free);
}

export function hasAccess(entry: ModuleEntry): boolean {
  if (DEV_UNLOCK) return true;
  return isFree(entry);
}
