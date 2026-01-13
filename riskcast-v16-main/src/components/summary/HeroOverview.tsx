import { Plane, Ship, Truck } from 'lucide-react';
import type { ShipmentData } from './types';

interface HeroOverviewProps {
  data: ShipmentData;
}

export function HeroOverview({ data }: HeroOverviewProps) {
  const ModeIcon = data.trade.mode === 'AIR' ? Plane : data.trade.mode === 'SEA' ? Ship : Truck;

  return (
    <div className="backdrop-blur-xl bg-gradient-to-br from-white/10 to-white/5 border border-white/10 rounded-[24px] p-8 shadow-[0_8px_32px_rgba(0,0,0,0.3)]">
      <div className="grid grid-cols-6 gap-8">
        {/* Route */}
        <div className="col-span-2">
          <div className="text-cyan-400/70 text-xs uppercase tracking-wider mb-3">Route</div>
          <div className="flex items-center gap-4">
            <div className="text-center">
              <div className="text-white/90 text-2xl">{data.trade.pol}</div>
              <div className="text-white/50 text-xs mt-1">{data.trade.polCity}</div>
            </div>
            
            <div className="flex-1 flex items-center gap-2">
              <div className="h-px flex-1 bg-gradient-to-r from-cyan-500/50 to-teal-500/50" />
              <ModeIcon className="w-5 h-5 text-cyan-400" />
              <div className="h-px flex-1 bg-gradient-to-r from-teal-500/50 to-cyan-500/50" />
            </div>
            
            <div className="text-center">
              <div className="text-white/90 text-2xl">{data.trade.pod}</div>
              <div className="text-white/50 text-xs mt-1">{data.trade.podCity}</div>
            </div>
          </div>
        </div>

        {/* Mode */}
        <div>
          <div className="text-cyan-400/70 text-xs uppercase tracking-wider mb-3">Transport Mode</div>
          <div className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#00D9FF]/20 border border-[#00D9FF]/30 rounded-xl">
            <ModeIcon className="w-4 h-4 text-cyan-400" />
            <span className="text-white">{data.trade.mode}</span>
          </div>
        </div>

        {/* Container */}
        <div>
          <div className="text-cyan-400/70 text-xs uppercase tracking-wider mb-3">Container</div>
          <div className="text-white/90">{data.trade.container_type}</div>
          <div className="text-white/50 text-sm mt-1">{data.trade.mode === 'AIR' ? 'Air Cargo Unit' : 'Container'}</div>
        </div>

        {/* Transit & Weight */}
        <div>
          <div className="text-cyan-400/70 text-xs uppercase tracking-wider mb-3">Transit & Weight</div>
          <div className="text-white/90">{data.trade.transit_time_days} days</div>
          <div className="text-white/50 text-sm mt-1">{data.cargo.gross_weight_kg.toLocaleString()} kg</div>
          <div className="text-white/40 text-xs mt-1">{data.cargo.volume_cbm} CBM</div>
        </div>

        {/* Shipment Value */}
        <div>
          <div className="text-cyan-400/70 text-xs uppercase tracking-wider mb-3">Shipment Value</div>
          <div className="text-white/90 text-xl">${data.value.toLocaleString()}</div>
          <div className="text-white/50 text-sm mt-1">USD</div>
        </div>
      </div>

      {/* Bottom Status Bar */}
      <div className="mt-6 pt-6 border-t border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-white/70 text-sm">Ready for Analysis</span>
          </div>
          <div className="text-white/40 text-xs">Updated just now</div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-white/50 text-sm">Data Confidence:</span>
          <div className="flex items-center gap-2">
            <div className="w-32 h-1 bg-white/10 rounded-full overflow-hidden">
              <div className="h-full w-[95%] bg-gradient-to-r from-cyan-500 to-teal-500 rounded-full" />
            </div>
            <span className="text-teal-400 text-sm">95%</span>
          </div>
        </div>
      </div>
    </div>
  );
}

