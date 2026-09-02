// Match the count attached to the reported outcome, never the largest number
// elsewhere in a sentence (dates, deployed personnel or district breakdowns).
function normalizeNumbers(text) {
  let out=String(text||'');
  out=out.replace(/[०-९]/g,d=>'०१२३४५६७८९'.indexOf(d));
  out=out.replace(/(\d{1,3})\s*(?:लाख|lakh)\s*(?:(\d{1,3})\s*(?:हजार|thousand))?\s*(\d{1,3})?/gi,(_,l,t='',r='')=>String(Number(l)*100000+Number(t||0)*1000+Number(r||0)));
  out=out.replace(/(\d{1,3})\s*(?:हजार|thousand)\s*(\d{1,3})?/gi,(_,t,r='')=>String(Number(t)*1000+Number(r||0)));
  return out.replace(/,/g,'').replace(/\s+/g,' ');
}
export function extract(text, kind) {
  const cleaned=normalizeNumbers(String(text||'').replace(/<[^>]*>/g,' '));
  const patterns={
    death:[/death toll\s+(?:(?:has\s+)?(?:risen|increased|climbed)\s+to|(?:has\s+)?reached|stands?\s+at|is|of)\s+(\d+)\b/gi,/bodies\s+of\s+(\d+)\s+(?:people|persons)\s+who\s+died/gi,/total\s+of\s+(\d+)\s+(?:people|persons)\s+(?:have\s+died|were\s+killed)/gi,/(?:मृत्यु\s+हुनेको\s+संख्या|मृतक\s+संख्या)\s*(\d+)\b/gi,/(\d+)\s*जनाको\s+(?:शव\s+(?:फेला|भेटि)|मृत्यु)/gi],
    missing:[/(?:more than|over|total of)\s+(\d+)\s+(?:people|persons)\b[^.!?।]{0,220}?\b(?:still\s+|remain\s+|are\s+)?missing/gi,/(\d+)\s+(?:people|persons)\s+(?:are\s+)?(?:still|remain)\s+missing/gi,/(?:अझै|हालसम्म)?\s*(\d+)\s*जना\s+(?:अझै\s+)?(?:सम्पर्कविहीन|बेपत्ता)/gi],
    rescued:[/(\d+)\s+(?:people|persons)\b[^.!?।]{0,100}?\bhave\s+been\s+rescued/gi,/(?:total of)\s+(\d+)\b[^.!?।]{0,100}?\brescued/gi,/(?:हालसम्म[^.!?।]{0,120}?)?(\d+)\s*जनाको\s+उद्धार/gi,/(\d+)\s*(?:को|जनालाई)\s+उद्धार/gi]
  };
  const values=[];
  for(const re of patterns[kind]||[])for(const match of cleaned.matchAll(re)){
    const n=Number(match[1]);if(Number.isSafeInteger(n)&&n>=0)values.push(n);
  }
  // Ambiguous conflicting totals require review, rather than picking the largest.
  const unique=[...new Set(values)];return unique.length===1?unique[0]:null;
}
