export const formatPercent = (value: number): string => `${(value * 100).toFixed(1)}%`;

export const formatNumber = (value: number): string => value.toLocaleString();

export const formatRelativeSeconds = (isoTs: string): string => {
  const deltaSec = Math.max(0, Math.floor((Date.now() - new Date(isoTs).getTime()) / 1000));
  if (deltaSec < 60) return `${deltaSec}s ago`;
  const minutes = Math.floor(deltaSec / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
};

export const isInternalIp = (ip: string): boolean => {
  if (ip.startsWith('10.')) return true;
  if (ip.startsWith('192.168.')) return true;
  const second = Number(ip.split('.')[1] ?? '-1');
  return ip.startsWith('172.') && second >= 16 && second <= 31;
};
