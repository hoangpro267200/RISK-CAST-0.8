import { Package, MapPin, Calendar, Ship, Clock } from 'lucide-react';
import type { ShipmentData } from '../types';

interface ShipmentHeaderProps {
  data: ShipmentData;
}

export function ShipmentHeader({ data }: ShipmentHeaderProps) {
  return (
    <div className="flex items-center justify-between p-6 bg-black/20 rounded-2xl border border-white/10 backdrop-blur-sm">
      <div className="flex items-center gap-6">
        <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20">
          <Package className="w-6 h-6 text-blue-400" />
        </div>

        <div>
          <h1 className="text-2xl font-semibold text-white">Shipment {data.shipmentId}</h1>
          <div className="flex items-center gap-4 mt-2 text-sm text-white/60">
            <div className="flex items-center gap-1">
              <MapPin className="w-4 h-4" />
              {data.route.pol} → {data.route.pod}
            </div>
            <div className="flex items-center gap-1">
              <Ship className="w-4 h-4" />
              {data.carrier}
            </div>
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              ETD: {data.etd}
            </div>
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              ETA: {data.eta}
            </div>
          </div>
        </div>
      </div>

      <div className="text-right">
        <div className="text-sm text-white/60">Data Confidence</div>
        <div className="text-2xl font-semibold text-white mt-1">
          {Math.round((data.dataConfidence ?? 0) * 100)}%
        </div>
        <div className="text-xs text-white/40 mt-1">Last updated: {data.lastUpdated}</div>
      </div>
    </div>
  );
}




