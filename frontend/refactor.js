const fs = require('fs');
const path = require('path');

const dashboardDir = path.join(__dirname, 'src', 'app', 'dashboard');

const replacements = [
    { regex: /var\(--text-primary\)/g, replacement: 'hsl(var(--foreground))' },
    { regex: /var\(--text-secondary\)/g, replacement: 'hsl(var(--muted-foreground))' },
    { regex: /var\(--text-tertiary\)/g, replacement: 'hsl(var(--muted-foreground))' }, // Simplified
    { regex: /var\(--bg-base\)/g, replacement: 'hsl(var(--background))' },
    { regex: /var\(--bg-surface\)/g, replacement: 'hsl(var(--card))' },
    { regex: /var\(--bg-overlay\)/g, replacement: 'hsl(var(--muted))' },
    { regex: /var\(--border-default\)/g, replacement: 'hsl(var(--border))' },
    { regex: /var\(--border-subtle\)/g, replacement: 'hsl(var(--border))' },
    { regex: /var\(--glass-bg\)/g, replacement: 'hsl(var(--muted))' },
    { regex: /var\(--accent-emerald\)/g, replacement: '10 180 120' }, // Approximate raw hsl for emerald
    { regex: /var\(--accent-rose\)/g, replacement: '350 100 60' },
    { regex: /var\(--accent-cyan\)/g, replacement: 'hsl(var(--primary))' },
    { regex: /var\(--accent-purple\)/g, replacement: 'hsl(var(--primary))' },
    { regex: /var\(--accent-blue\)/g, replacement: 'hsl(var(--primary))' },
    { regex: /glass-card/g, replacement: 'bg-card border text-card-foreground shadow-sm rounded-xl' },
    { regex: /text-gradient-brand/g, replacement: 'text-primary' },
    { regex: /bg-gradient-to-r from-\[.*?\] to-\[.*?\]/g, replacement: 'bg-primary' },
    { regex: /bg-gradient-to-br from-\[.*?\] to-\[.*?\]/g, replacement: 'bg-primary' },
    { regex: /hover:shadow-\[var\(--accent-cyan\)]\/25/g, replacement: 'hover:shadow-sm' },
    { regex: /hover:border-white\/\[0\.15\]/g, replacement: 'hover:border-primary/50' },
    { regex: /hover:shadow-\[0_0_25px_rgba\(.*?\)\]/g, replacement: 'hover:shadow-md' },
    // Fix specific tailwind patterns that get mangled by raw replacement:
    { regex: /text-\[hsl\(var\(--foreground\)\)\]/g, replacement: 'text-foreground' },
    { regex: /text-\[hsl\(var\(--muted-foreground\)\)\]/g, replacement: 'text-muted-foreground' },
    { regex: /bg-\[hsl\(var\(--background\)\)\]/g, replacement: 'bg-background' },
    { regex: /bg-\[hsl\(var\(--card\)\)\]/g, replacement: 'bg-card' },
    { regex: /bg-\[hsl\(var\(--muted\)\)\]/g, replacement: 'bg-muted' },
    { regex: /border-\[hsl\(var\(--border\)\)\]/g, replacement: 'border-border' },
];

function processDirectory(dir) {
    const files = fs.readdirSync(dir);
    for (const file of files) {
        const fullPath = path.join(dir, file);
        const stat = fs.statSync(fullPath);
        if (stat.isDirectory()) {
            processDirectory(fullPath);
        } else if (fullPath.endsWith('.tsx') || fullPath.endsWith('.ts')) {
            let content = fs.readFileSync(fullPath, 'utf8');
            let originalContent = content;
            for (const { regex, replacement } of replacements) {
                content = content.replace(regex, replacement);
            }
            if (content !== originalContent) {
                fs.writeFileSync(fullPath, content, 'utf8');
                console.log(`Updated ${fullPath}`);
            }
        }
    }
}

processDirectory(dashboardDir);
console.log('Refactoring complete.');
