import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import { MountainWaveTerrainResearch } from "./MountainWaveTerrainResearch";

const isMountainWaveTerrainResearch =
  window.location.pathname === "/research/mountain-wave-terrain";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {isMountainWaveTerrainResearch ? <MountainWaveTerrainResearch /> : <App />}
  </StrictMode>,
);
