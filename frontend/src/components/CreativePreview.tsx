import React from 'react';
import { Type, FileText, MousePointer, Download, Image as ImageIcon } from 'lucide-react';
import type { GeneratedAd, GeneratedAsset } from '../types';

interface Props {
  ad: GeneratedAd;
  assets?: GeneratedAsset[];
}

function parseAsset(asset: GeneratedAsset): any {
  try { return asset.content ? JSON.parse(asset.content) : {}; } catch { return {}; }
}

export default function CreativePreview({ ad, assets = [] }: Props) {
  const visualAssets = assets
    .filter((asset) => asset.asset_type === 'static_image' || asset.asset_type === 'carousel_image')
    .map(parseAsset)
    .filter((asset) => asset.image_url);

  return (
    <div className="space-y-6">
      <div className="card overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-lg font-bold text-gray-900">Generated Ad</h2>
        </div>
        <div className="p-6 space-y-4">
          <div><div className="flex items-center gap-2 text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1"><Type className="w-3.5 h-3.5" /> Headline</div><p className="text-xl font-bold text-gray-900">{ad.headline}</p></div>
          <div><div className="flex items-center gap-2 text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1"><FileText className="w-3.5 h-3.5" /> Primary Copy</div><p className="text-gray-700 leading-relaxed">{ad.primary_copy}</p></div>
          <div><div className="flex items-center gap-2 text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1"><MousePointer className="w-3.5 h-3.5" /> CTA</div><span className="inline-block px-5 py-2.5 bg-brand-600 text-white rounded-lg font-semibold text-sm">{ad.cta}</span></div>
        </div>
      </div>

      {visualAssets.length > 0 && (
        <div className="card overflow-hidden">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2"><ImageIcon className="w-5 h-5 text-brand-600" /> Product-grounded visual creative</h2>
            <p className="text-sm text-gray-500 mt-1">The exact uploaded product photo is preserved. DevAd adds a product-specific photographic backdrop, shadow, composition and deterministic text — with no paid visual API.</p>
          </div>
          <div className={`p-6 grid gap-5 ${visualAssets.length > 1 ? 'sm:grid-cols-3' : 'max-w-xl mx-auto'}`}>
            {visualAssets.map((asset, index) => (
              <div key={index} className="rounded-xl overflow-hidden border border-gray-100 bg-gray-50">
                <img src={asset.image_url} alt={`Generated product creative ${index + 1}`} className="w-full block" />
                <div className="p-3 flex items-center justify-between"><span className="text-xs text-gray-500">{asset.provider === 'local-product-poster' ? 'Zero-cost product poster' : asset.provider}</span><a href={asset.image_url} download className="btn-secondary text-xs py-1.5 px-2.5"><Download className="w-3.5 h-3.5" /> JPG/PNG</a></div>
              </div>
            ))}
          </div>
        </div>
      )}



    </div>
  );
}
