import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import { MountainWaveTerrainResearch } from "./MountainWaveTerrainResearch";
import { StormExaminationResearch } from "./StormExaminationResearch";

const isMountainWaveTerrainResearch =
  window.location.pathname === "/research/mountain-wave-terrain";
const isStormExaminationResearch = window.location.pathname === "/research/storm-examination";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {isMountainWaveTerrainResearch ? (
      <MountainWaveTerrainResearch />
    ) : isStormExaminationResearch ? (
      <StormExaminationResearch />
    ) : (
      <App />
    )}
  </StrictMode>,
);
