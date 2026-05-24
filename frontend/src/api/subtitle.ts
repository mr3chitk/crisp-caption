export async function startSubtitleOverlay(): Promise<boolean> {
  const response = await fetch('/overlay/start', { method: 'POST' });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Overlay start failed (${response.status})`);
  }
  return true;
}
