import type { ConfigProfile } from '@/types';

export interface ProfilesResponse {
  profiles: ConfigProfile[];
  active: string;
  crisp_status: string;
}

export async function fetchProfiles(): Promise<ProfilesResponse> {
  const response = await fetch('/profiles');
  if (!response.ok) {
    throw new Error(`GET /profiles failed ${response.status}`);
  }
  return (await response.json()) as ProfilesResponse;
}

export async function selectProfile(name: string): Promise<ProfilesResponse> {
  const response = await fetch('/profiles/select', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  if (!response.ok) {
    let detail = `POST /profiles/select failed ${response.status}`;
    try {
      const data = (await response.json()) as { error?: string };
      if (data.error) detail += `: ${data.error}`;
    } catch {
      // Keep the HTTP status as the actionable error.
    }
    throw new Error(detail);
  }
  return (await response.json()) as ProfilesResponse;
}
