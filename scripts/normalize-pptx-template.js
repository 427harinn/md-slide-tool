#!/usr/bin/env node

import fs from "fs";
import path from "path";
import AdmZip from "adm-zip";

const inputPath = process.argv[2];

if (!inputPath) {
    console.error("使い方: node scripts/normalize-pptx-template.js <template.pptx>");
    process.exit(1);
}

if (!fs.existsSync(inputPath)) {
    console.error(`ファイルが見つかりません: ${inputPath}`);
    process.exit(1);
}

const layoutNameMap = {
    "タイトル スライド": "Title Slide",
    "タイトルスライド": "Title Slide",
    "セクション見出し": "Section Header",
    "タイトルとコンテンツ": "Title and Content",
    "2 つのコンテンツ": "Two Content",
    "2つのコンテンツ": "Two Content",
    "比較": "Comparison",
    "キャプション付きのコンテンツ": "Content with Caption",
    "空白": "Blank"
};

function replaceAttribute(xml, attrName, from, to) {
    const escapedFrom = from.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const regex = new RegExp(`(${attrName}=")${escapedFrom}(")`, "g");
    return xml.replace(regex, `$1${to}$2`);
}

const absInput = path.resolve(inputPath);
const zip = new AdmZip(absInput);
const entries = zip.getEntries();

let changedCount = 0;

for (const entry of entries) {
    if (!entry.entryName.startsWith("ppt/slideLayouts/slideLayout") || !entry.entryName.endsWith(".xml")) {
        continue;
    }

    let xml = entry.getData().toString("utf8");
    const originalXml = xml;

    for (const [jp, en] of Object.entries(layoutNameMap)) {
        xml = replaceAttribute(xml, "name", jp, en);
        xml = replaceAttribute(xml, "matchingName", jp, en);
    }

    if (xml !== originalXml) {
        zip.updateFile(entry.entryName, Buffer.from(xml, "utf8"));
        changedCount++;
    }
}

zip.writeZip(absInput);

console.log(`正規化しました: ${absInput}`);
console.log(`更新したレイアウトXML数: ${changedCount}`);