import { SEGMENT_NRR } from "@/lib/data/product";
import { AMBER, BRAND } from "@/lib/palette";

/** NRR by segment on a fixed 80–120% axis; segments below 100% are shown in amber. */
const AXIS: [number, number] = [80, 120];

export function SegmentBars() {
  return (
    <>
      {SEGMENT_NRR.map(({ segment, nrr }) => (
        <div key={segment} className="hb">
          <span className="hb-l">{segment}</span>
          <span className="hb-t">
            <i
              style={{
                width: `${(((nrr - AXIS[0]) / (AXIS[1] - AXIS[0])) * 100).toFixed(0)}%`,
                background: nrr >= 100 ? BRAND : AMBER,
              }}
            />
          </span>
          <b>{nrr.toFixed(0)}%</b>
        </div>
      ))}
    </>
  );
}
