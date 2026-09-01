// Match the count attached to the reported outcome, never the largest number
// elsewhere in a sentence (dates, deployed personnel or district breakdowns).
export function extract(text, kind) {
  const cleaned=String(text||'').replace(/<[^>]*>/g,' ').replace(/,/g,'').replace(/\s+/g,' ');
  const patterns={
    death:[/death toll\s+(?:(?:has\s+)?(?:risen|increased|climbed)\s+to|(?:has\s+)?reached|stands?\s+at|is|of)\s+(\d+)\b/gi,/bodies\s+of\s+(\d+)\s+(?:people|persons)\s+who\s+died/gi,/total\s+of\s+(\d+)\s+(?:people|persons)\s+(?:have\s+died|were\s+killed)/gi],
    missing:[/(?:more than|over|total of)\s+(\d+)\s+(?:people|persons)\b[^.!?।]{0,220}?\b(?:still\s+|remain\s+|are\s+)?missing/gi,/(\d+)\s+(?:people|persons)\s+(?:are\s+)?(?:still|remain)\s+missing/gi],
    rescued:[/(\d+)\s+(?:people|persons)\b[^.!?।]{0,100}?\bhave\s+been\s+rescued/gi,/(?:total of)\s+(\d+)\b[^.!?।]{0,100}?\brescued/gi]
  };
  const values=[];
  for(const re of patterns[kind]||[])for(const match of cleaned.matchAll(re)){
    const n=Number(match[1]);if(Number.isSafeInteger(n)&&n>=0)values.push(n);
  }
  // Ambiguous conflicting totals require review, rather than picking the largest.
  const unique=[...new Set(values)];return unique.length===1?unique[0]:null;
}
