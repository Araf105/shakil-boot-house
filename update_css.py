import os

templates_dir = 'templates'
css_link = '    <link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/style.css\') }}">\n</head>'

for filename in os.listdir(templates_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(templates_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Jodi already link na thake, tahole </head> er age bosiye dibe
        if 'css/style.css' not in content:
            if '</head>' in content:
                content = content.replace('</head>', css_link)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Updated: {filename}")

print("Shob file-e successfully CSS link add hoye geche!")