#!/usr/bin/env node

import fs from "fs";
import path from "path";
import { Command } from "commander";
import { fileURLToPath } from "url";
import { spawn } from "child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..");

const program = new Command();

program
    .name("slidegen")
    .description("Markdown / Quarto project generator")
    .version("1.0.0");

program
    .command("new")
    .description("新しいプロジェクトを作成する")
    .argument("<name>", "プロジェクト名")
    .requiredOption("--type <type>", "出力形式 (pptx/docx/html)")
    .option(
        "--template <template>",
        "テンプレート名（省略時: template）",
        "template"
    )
    .action((name, options) => {
        const type = options.type;
        const template = options.template;

        const templatesRoot = path.join(rootDir, "templates");

        if (!fs.existsSync(templatesRoot)) {
            console.error("templates フォルダが見つかりません");
            process.exit(1);
        }

        const supportedTypes = fs.readdirSync(templatesRoot).filter((entry) => {
            const fullPath = path.join(templatesRoot, entry);
            return fs.statSync(fullPath).isDirectory();
        });

        if (!supportedTypes.includes(type)) {
            console.error(`未対応の type です: ${type}`);
            console.error(`利用可能: ${supportedTypes.join(", ")}`);
            process.exit(1);
        }

        const projectDir = path.join(rootDir, "projects", name);
        const imgDir = path.join(projectDir, "img");
        const readmePath = path.join(projectDir, "README.md");
        const qmdFileName = `${name}_${type}.qmd`;
        const qmdFilePath = path.join(projectDir, qmdFileName);

        const templatePath = path.join(rootDir, "templates", type, `${template}.qmd`);

        if (!fs.existsSync(templatePath)) {
            console.error(`テンプレートが見つかりません: ${templatePath}`);
            process.exit(1);
        }

        fs.mkdirSync(imgDir, { recursive: true });

        if (!fs.existsSync(readmePath)) {
            fs.writeFileSync(readmePath, `# ${name}\n`, "utf8");
        }

        if (fs.existsSync(qmdFilePath)) {
            console.error(`すでに存在します: ${qmdFilePath}`);
            process.exit(1);
        }

        const templateContent = fs.readFileSync(templatePath, "utf8");
        const outputContent = templateContent.replaceAll("{{TITLE}}", name);

        fs.writeFileSync(qmdFilePath, outputContent, "utf8");

        console.log(`作成しました: ${qmdFilePath}`);

        spawn("code", [qmdFilePath], {
            stdio: "inherit",
            shell: true,
        });
    });

program
    .command("list-templates")
    .description("利用可能なテンプレート一覧を表示")
    .action(() => {
        const templatesRoot = path.join(rootDir, "templates");

        if (!fs.existsSync(templatesRoot)) {
            console.error("templates フォルダが見つかりません");
            process.exit(1);
        }

        const types = fs.readdirSync(templatesRoot);

        types.forEach((type) => {
            const typePath = path.join(templatesRoot, type);

            if (!fs.statSync(typePath).isDirectory()) return;

            const files = fs.readdirSync(typePath);

            const templates = files
                .filter((file) => file.endsWith(".qmd"))
                .map((file) => file.replace(".qmd", ""));

            if (templates.length > 0) {
                console.log(`${type}:`);
                templates.forEach((t) => {
                    if (t === "template") {
                        console.log(`  - ${t} (default)`);
                    } else {
                        console.log(`  - ${t}`);
                    }
                });
                console.log("");
            }
        });
    });

program.parse(process.argv);