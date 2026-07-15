const fs = require('fs');
const path = require('path');
const dir = 'E:/SPEC/src/components/views';
const files = fs.readdirSync(dir).filter(f => f.endsWith('.tsx'));

for (const file of files) {
  const p = path.join(dir, file);
  let c = fs.readFileSync(p, 'utf8');
  
  if (c.includes('<table') && !c.includes('overflow-x-auto')) {
      c = c.replace(/(<table[^>]*>)/g, '<div className="overflow-x-auto">\n$1');
      c = c.replace(/(<\/table>)/g, '$1\n</div>');
      fs.writeFileSync(p, c);
      console.log('Wrapped table in ' + file);
  }
}
