/** TalkingHead-compatible GLB presets (Mixamo rig + ARKit + Oculus visemes). */
const CDN =
  "https://cdn.jsdelivr.net/gh/met4citizen/TalkingHead@main/avatars";

export type AvatarPreset = {
  url: string;
  body: "M" | "F";
  avatarMood: string;
  lipsyncLang: string;
  retarget?: Record<string, unknown>;
  baseline?: Record<string, number>;
};

/** Studio lighting — TalkingHead defaults (ambient 2, direct 30), not the broken 1.05 we had. */
export const STUDIO_LIGHTING = {
  lightAmbientColor: 0xfff8f0,
  lightAmbientIntensity: 2.4,
  lightDirectColor: 0xffe4c8,
  lightDirectIntensity: 28,
  lightDirectPhi: 1,
  lightDirectTheta: 2.1,
  lightSpotColor: 0xa8c8ff,
  lightSpotIntensity: 0.85,
  lightSpotPhi: 0.12,
  lightSpotTheta: 3.6,
  lightSpotDispersion: 0.9,
};

export function getAvatarPreset(audience?: string | null): AvatarPreset {
  if (audience === "child") {
    return {
      url: "/models/child-boy.glb",
      body: "M",
      avatarMood: "happy",
      lipsyncLang: "en",
      baseline: {
        headRotateX: -0.08,
        eyeBlinkLeft: 0.05,
        eyeBlinkRight: 0.05,
      },
    };
  }

  // Male photoreal teacher (Илья) — AvatarSDK + official retarget from TalkingHead siteconfig
  return {
    url: `${CDN}/avatarsdk.glb`,
    body: "M",
    avatarMood: "neutral",
    lipsyncLang: "en",
    retarget: {
      Neck: { z: -0.01, rx: -0.15 },
      Neck1: { z: -0.01, rx: -0.15 },
      Neck2: { z: -0.01, rx: -0.15 },
      LeftShoulder: { rz: -0.3 },
      RightShoulder: { rz: 0.3 },
      scaleToEyesLevel: 1.0,
      origin: { y: -0.1 },
    },
    baseline: {
      headRotateX: -0.04,
      eyeBlinkLeft: 0.05,
      eyeBlinkRight: 0.05,
    },
  };
}
