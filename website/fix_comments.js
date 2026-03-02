const fs = require('fs');
const filepath = '/Volumes/AppDen/AppsHom/bijmantra/website/src/pages/index.tsx';
let content = fs.readFileSync(filepath, 'utf8');

// Also handle the style attribute which might be a string in HTML but needs to be an object in React
content = content.replace(/<!--([\s\S]*?)-->/g, '{/*$1*/}');

fs.writeFileSync(filepath, content);
console.log('Fixed HTML comments in index.tsx');
