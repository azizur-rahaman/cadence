import { expect, test } from "@playwright/test";

const API_URL = process.env.E2E_API_URL || "http://localhost:8000";

async function loginApi(userId: string): Promise<string> {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  if (!res.ok) throw new Error(`Login failed for ${userId}: ${res.status}`);
  const body = (await res.json()) as { data: { access_token: string } };
  return body.data.access_token;
}

async function ensureNoActiveMeeting(teamId: string): Promise<void> {
  const adminToken = await loginApi("u1");
  const activeRes = await fetch(`${API_URL}/api/v1/teams/${teamId}/meetings/active`, {
    headers: { Authorization: `Bearer ${adminToken}` },
  });
  if (!activeRes.ok) return;
  const body = (await activeRes.json()) as {
    data: { meeting: { id: string; facilitator_id: string } | null };
  };
  const active = body.data.meeting;
  if (!active) return;
  const facToken = await loginApi(active.facilitator_id);
  await fetch(`${API_URL}/api/v1/meetings/${active.id}/end`, {
    method: "POST",
    headers: { Authorization: `Bearer ${facToken}` },
  });
}

test.describe("Two-Browser Live Level 10 Meeting Sync", () => {
  test.beforeEach(async () => {
    await ensureNoActiveMeeting("team_lead");
  });

  test("facilitator and attendee sync sections, reload cleanly, rate, and view immutable summary", async ({
    browser,
  }) => {
    const ctx1 = await browser.newContext();
    const ctx2 = await browser.newContext();
    const page1 = await ctx1.newPage();
    const page2 = await ctx2.newPage();

    try {
      // Browser 1: Switch to Blake Brooks (u2, Team Member, Facilitator)
      await page1.goto("/");
      await expect(page1.getByLabel("User Switcher")).toBeVisible();
      await page1.getByLabel("User Switcher").selectOption("u2");
      await expect(page1.getByText(/Signed in as Blake Brooks/i)).toBeVisible();

      // Browser 2: Switch to Casey Cho (u3, Team Member, Attendee)
      await page2.goto("/");
      await expect(page2.getByLabel("User Switcher")).toBeVisible();
      await page2.getByLabel("User Switcher").selectOption("u3");
      await expect(page2.getByText(/Signed in as Casey Cho/i)).toBeVisible();

      // Browser 1 starts the Level 10 Meeting
      await page1.getByRole("button", { name: /Start Level 10/i }).click();
      await expect(page1).toHaveURL(/\/meetings\/mt_/);
      const meetingUrl = page1.url();
      await expect(page1.getByTestId("meeting-timer")).toBeVisible();

      // Browser 2 joins the same live meeting
      await page2.goto(meetingUrl);
      await expect(page2.getByTestId("meeting-timer")).toBeVisible();

      // Both browsers see both attendees (Dan Park & Maya Patel)
      await expect(page1.getByText(/Attendees \(2\)/)).toBeVisible();
      await expect(page2.getByText(/Attendees \(2\)/)).toBeVisible();

      // Browser 1 advances Scorecard -> IDS; Browser 2 syncs automatically
      await page1.getByRole("button", { name: /Next: IDS/i }).click();
      await expect(page1.getByRole("heading", { name: /Issues \(IDS\)/i })).toBeVisible();
      await expect(page2.getByRole("heading", { name: /Issues \(IDS\)/i })).toBeVisible();

      // Browser 2 reloads mid-meeting and recovers into IDS cleanly
      await page2.reload();
      await expect(page2.getByRole("heading", { name: /Issues \(IDS\)/i })).toBeVisible();

      // Browser 1 advances IDS -> Conclude; Browser 2 syncs
      await page1.getByRole("button", { name: /Next: Conclude/i }).click();
      await expect(page1.getByRole("heading", { name: /Rate This Meeting/i })).toBeVisible();
      await expect(page2.getByRole("heading", { name: /Rate This Meeting/i })).toBeVisible();

      // Both participants rate: Dan = 8, Maya = 9 -> Average = 8.5
      await page1.getByRole("button", { name: "Rate meeting 8 out of 10" }).click();
      await page2.getByRole("button", { name: "Rate meeting 9 out of 10" }).click();
      await expect(page1.getByText(/Average:\s*8\.5/)).toBeVisible();
      await expect(page2.getByText(/Average:\s*8\.5/)).toBeVisible();

      // Facilitator ends the meeting -> both browsers show immutable summary with 8.5 / 10
      await page1.getByRole("button", { name: /End Meeting/i }).click();
      await expect(page1.getByTestId("meeting-summary")).toBeVisible();
      await expect(page2.getByTestId("meeting-summary")).toBeVisible();
      await expect(page2.getByText("8.5 / 10")).toBeVisible();
    } finally {
      await ctx1.close();
      await ctx2.close();
    }
  });
});
