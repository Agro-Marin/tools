#!/usr/bin/env python3
"""
Odoo XML Formatter using xmllint (preserves comments)
Formats XML files with 4-space indentation and proper spacing
"""

import sys
import subprocess
from pathlib import Path


def format_odoo_xml(file_path: Path) -> None:
    """Format an Odoo XML file using xmllint (preserves comments and applies 4-space indentation)."""
    try:
        # Step 1: Use xmllint to format XML (preserves comments)
        result = subprocess.run(
            [
                "xmllint", 
                "--format",
                "--encode", "utf-8",
                str(file_path),
                "--output", str(file_path)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"✗ Error formatting {file_path}: {result.stderr}")
            return
            
        # Step 2: Apply custom 4-space indentation (xmllint uses 2 spaces by default)
        _apply_custom_indentation(file_path)
        
        # Step 3: Apply advanced formatting rules (after xmllint to override its compacting)
        _apply_advanced_formatting(file_path)
        
        # Step 4: Pre-process to preserve multiline expressions
        _preserve_multiline_expressions(file_path)
        
        # Step 5: Post-process to fix any remaining issues
        _fix_domain_attributes(file_path)
        
        # Step 6: Fix mixed content indentation
        _fix_mixed_content_indentation(file_path)
        
        # Step 7: Clean up empty lines with whitespace
        _clean_empty_lines(file_path)
        
        print(f"✓ Formatted: {file_path}")
            
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout formatting {file_path}")
    except FileNotFoundError:
        print(f"✗ xmllint not found. Install with: sudo apt-get install libxml2-utils")
    except Exception as e:
        print(f"✗ Error formatting {file_path}: {e}")


def _apply_custom_indentation(file_path: Path) -> None:
    """Convert xmllint's 2-space indentation to 4-space indentation to match tabWidth config."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Convert 2-space indentation to 4-space indentation
        lines = content.split('\n')
        converted_lines = []
        
        for line in lines:
            # Count leading spaces
            leading_spaces = len(line) - len(line.lstrip())
            
            if leading_spaces > 0 and leading_spaces % 2 == 0:
                # Convert 2-space indentation to 4-space
                new_indent_level = (leading_spaces // 2) * 4
                converted_line = ' ' * new_indent_level + line.lstrip()
                converted_lines.append(converted_line)
            else:
                # Keep line as is (no indentation or odd spacing)
                converted_lines.append(line)
        
        converted_content = '\n'.join(converted_lines)
        
        # Only write if content changed
        if converted_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(converted_content)
                
    except Exception as e:
        print(f"⚠️  Warning: Could not apply custom indentation to {file_path}: {e}")


def _apply_advanced_formatting(file_path: Path) -> None:
    """Apply advanced formatting rules like printWidth=119, self-closing spaces, etc."""
    import re
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. Add space before self-closing tags ONLY (xmlSelfClosingSpace: true)
        content = re.sub(r'([^/\s])(/>)', r'\1 \2', content)  # Only for self-closing />
        
        # 2. Handle long lines (printWidth: 119) - break long attribute lists
        content = _break_long_lines(content)
        
        # 3. Normalize spacing in attributes
        content = re.sub(r'=\s*"', '="', content)  # Remove space before quote
        content = re.sub(r'=\s*\'', "='", content)  # Remove space before single quote
        
        # Write back if changed
        original_content = content
        with open(file_path, 'r', encoding='utf-8') as f:
            original = f.read()
        
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
    except Exception as e:
        print(f"⚠️  Warning: Could not apply advanced formatting to {file_path}: {e}")


def _break_long_lines(content: str) -> str:
    """Break long lines for ALL XML elements that exceed length or have multiple attributes."""
    import re
    lines = content.split('\n')
    formatted_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        
        # Skip comments, closing tags, and empty lines
        if (not stripped_line or 
            stripped_line.startswith('<!--') or 
            stripped_line.startswith('</')):
            formatted_lines.append(line)
            continue
            
        # Check for any XML element with attributes
        if '<' in line and '>' in line and '=' in line:
            # Detect attributes more comprehensively
            attr_count = len(re.findall(r'[\w:-]+\s*=\s*["\'][^"\']*["\']', line))
            line_length = len(line)
            
            # ONLY break if line is genuinely long AND has multiple attributes
            should_break = (
                line_length > 119 and attr_count >= 3
            )
            
            if should_break:
                formatted_line = _break_xml_attributes(line)
                if formatted_line and formatted_line != line:
                    # Successfully formatted, add multi-line result
                    formatted_lines.extend(formatted_line.split('\n'))
                else:
                    # Fallback to original
                    formatted_lines.append(line)
            else:
                formatted_lines.append(line)
        else:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)


def _break_xml_attributes(line: str) -> str:
    """Break XML attributes across multiple lines ONLY when truly necessary."""
    import re
    
    # Only break if line is actually long or has many attributes
    if len(line) <= 100:
        return line
    
    # Extract base indentation
    stripped_line = line.lstrip()
    indent = len(line) - len(stripped_line)
    base_indent = ' ' * indent
    attr_indent = ' ' * (indent + 4)
    
    # Match any opening tag (field, widget, button, etc.)
    tag_match = re.match(r'^<([\w:-]+)', stripped_line)
    if not tag_match:
        return line
    
    tag_name = tag_match.group(1)
    
    # Extract all attributes (including namespaced attributes like t-field)
    attr_pattern = r'([\w:-]+\s*=\s*(?:"[^"]*"|\'[^\']*\'))'
    closing_pattern = r'(\s*/?\s*>)\s*$'
    
    # Find all attributes
    attrs = re.findall(attr_pattern, stripped_line)
    closing_match = re.search(closing_pattern, stripped_line)
    
    # ONLY break if line is long AND has multiple attributes
    if len(attrs) >= 3 and len(line) > 119:
        result = f"{base_indent}<{tag_name}\n"
        
        # Add each attribute on its own line with proper indentation
        for attr in attrs:
            clean_attr = attr.strip()
            result += f"{attr_indent}{clean_attr}\n"
        
        # Add closing tag
        if closing_match:
            closing = closing_match.group(1).strip()
            result += f"{base_indent}{closing}"
        else:
            result += f"{base_indent}>"
        
        return result
    
    return line


def _preserve_multiline_expressions(file_path: Path) -> None:
    """Preserve proper spacing in multiline expressions."""
    import re
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to find attributes with very long single-line expressions
        long_attr_pattern = r'(\w+="[^"]{150,}")'
        
        def fix_long_attribute(match):
            attr_content = match.group(0)
            
            # Check if this looks like a collapsed Python expression
            if any(op in attr_content for op in [' or ', ' and ', ' not ', ' in ', '!=', '==']):
                # Apply spacing fixes
                fixed = attr_content
                
                # Fix operators that might be squished
                fixed = re.sub(r"(['\")])(or|and|not)([^\s])", r"\1 \2 \3", fixed)
                fixed = re.sub(r"([^\s])(or|and|not)([\(\'])", r"\1 \2 \3", fixed)
                fixed = re.sub(r"(['\)])in\(", r"\1 in (", fixed)
                fixed = re.sub(r"!=(['\(])", r"!= \1", fixed)
                fixed = re.sub(r"==(['\(])", r"== \1", fixed)
                
                return fixed
            
            return attr_content
        
        # Apply fixes to long attributes
        modified_content = re.sub(long_attr_pattern, fix_long_attribute, content)
        
        # Write back if changed
        if modified_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
                
    except Exception as e:
        print(f"⚠️  Warning: Could not preserve multiline expressions in {file_path}: {e}")


def _fix_domain_attributes(file_path: Path) -> None:
    """Fix formatting of Python expressions in XML attributes."""
    import re
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern 1: Attributes with Python lists (domain, filter_domain, context with lists)
        list_pattern = r'((?:filter_domain|domain|context)=")\[(.*?)\](")'
        
        def fix_list_content(match):
            prefix = match.group(1)  # 'filter_domain="['
            list_content = match.group(2)  # Content between brackets
            suffix = match.group(3)  # ']"'
            
            # Clean up the list content
            cleaned = re.sub(r'\s+', ' ', list_content.strip())
            cleaned = re.sub(r'\s*,\s*', ', ', cleaned)
            cleaned = re.sub(r"\s*'\s*", "'", cleaned)
            cleaned = re.sub(r'^\s+|\s+$', '', cleaned)
            
            return f"{prefix}[{cleaned}]{suffix}"
        
        # Pattern 2: Attributes with Python expressions (invisible, readonly, required, etc.)
        expr_pattern = r'((?:invisible|readonly|required|optional)=")\((.*?)\)(")'
        
        def fix_expression_content(match):
            prefix = match.group(1)  # 'invisible="('
            expr_content = match.group(2)  # Content between parentheses
            suffix = match.group(3)  # ')"'
            
            # Clean up the expression content
            # First normalize all whitespace
            cleaned = re.sub(r'\s+', ' ', expr_content.strip())
            
            # Format comparison operators (handle cases where they're attached to text)
            cleaned = re.sub(r'([^\s])!=([^\s])', r'\1 != \2', cleaned)
            cleaned = re.sub(r'([^\s])==([^\s])', r'\1 == \2', cleaned)
            cleaned = re.sub(r'([^\s])>=([^\s])', r'\1 >= \2', cleaned)
            cleaned = re.sub(r'([^\s])<=([^\s])', r'\1 <= \2', cleaned)
            cleaned = re.sub(r'([^\s><=!])>([^\s>=])', r'\1 > \2', cleaned)
            cleaned = re.sub(r'([^\s<>=!])<([^\s>=])', r'\1 < \2', cleaned)
            
            # Format logical operators with word boundaries to avoid breaking words
            # Handle 'or' as standalone word only
            cleaned = re.sub(r"(['\"\)])or\b", r"\1 or", cleaned)  # Before 'or'
            cleaned = re.sub(r"\bor([\(])", r"or \1", cleaned)      # After 'or'
            
            # Handle 'and' as standalone word only
            cleaned = re.sub(r"(['\"\)])and\b", r"\1 and", cleaned)  # Before 'and'
            cleaned = re.sub(r"\band([\(])", r"and \1", cleaned)      # After 'and'
            
            # Handle 'not' as standalone word only  
            cleaned = re.sub(r"(['\"\)])not\b", r"\1 not", cleaned)  # Before 'not'
            cleaned = re.sub(r"\bnot([\(])", r"not \1", cleaned)      # After 'not'
            
            # Handle 'in' as standalone word only
            cleaned = re.sub(r"(['\"\)])\bin\b", r"\1 in", cleaned)  # Before 'in'
            cleaned = re.sub(r"\bin([\(])", r"in \1", cleaned)        # After 'in'
            
            # Clean up any excessive spaces
            cleaned = re.sub(r'\s+', ' ', cleaned)
            
            # Clean up quotes and parentheses (preserve spaces around operators)
            # Only remove spaces inside quotes, not around them
            cleaned = re.sub(r"'\s+([^']*)\s+'", r"'\1'", cleaned)
            cleaned = re.sub(r'"\s+([^"]*)\s+"', r'"\1"', cleaned)
            # Only remove spaces immediately inside parentheses, not around them
            cleaned = re.sub(r'\(\s+', '(', cleaned)
            cleaned = re.sub(r'\s+\)', ')', cleaned)
            cleaned = re.sub(r'\s*,\s*', ', ', cleaned)
            
            # Remove leading/trailing whitespace
            cleaned = cleaned.strip()
            
            return f"{prefix}({cleaned}){suffix}"
        
        # Pattern 3: Simple context attributes (context with dicts)
        dict_pattern = r'(context=")\{(.*?)\}(")'
        
        def fix_dict_content(match):
            prefix = match.group(1)  # 'context="{'
            dict_content = match.group(2)  # Content between braces
            suffix = match.group(3)  # '}"'
            
            # Clean up the dict content
            cleaned = re.sub(r'\s+', ' ', dict_content.strip())
            cleaned = re.sub(r'\s*:\s*', ': ', cleaned)
            cleaned = re.sub(r'\s*,\s*', ', ', cleaned)
            cleaned = re.sub(r"\s*'\s*", "'", cleaned)
            cleaned = cleaned.strip()
            
            return f"{prefix}{{{cleaned}}}{suffix}"
        
        # Apply all fixes
        fixed_content = content
        fixed_content = re.sub(list_pattern, fix_list_content, fixed_content, flags=re.DOTALL)
        fixed_content = re.sub(expr_pattern, fix_expression_content, fixed_content, flags=re.DOTALL)
        fixed_content = re.sub(dict_pattern, fix_dict_content, fixed_content, flags=re.DOTALL)
        
        # Write back only if content changed
        if fixed_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
                
    except Exception as e:
        print(f"⚠️  Warning: Could not fix domain attributes in {file_path}: {e}")


def _fix_mixed_content_indentation(file_path: Path) -> None:
    """Fix over-indentation of text content within XML elements."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Look for opening tag followed by over-indented text
            if '<' in line and '>' in line and not line.strip().startswith('</') and not line.strip().endswith('/>'):
                # Check if next line is over-indented text content
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    
                    # Check if this looks like over-indented text content
                    if (next_line.strip() and 
                        not next_line.strip().startswith('<') and 
                        len(next_line) - len(next_line.lstrip()) > len(line) - len(line.lstrip()) + 8):
                        
                        # Find the closing tag
                        closing_tag_line = None
                        j = i + 1
                        while j < len(lines):
                            if '</' in lines[j]:
                                closing_tag_line = j
                                break
                            j += 1
                        
                        if closing_tag_line:
                            # Calculate correct indentation (opening tag + 4 spaces)
                            opening_indent = len(line) - len(line.lstrip())
                            content_indent = opening_indent + 4
                            
                            # Fix the text content indentation
                            fixed_lines.append(line)
                            
                            # Fix all lines between opening and closing tag
                            for k in range(i + 1, closing_tag_line):
                                text_line = lines[k]
                                if text_line.strip():  # Only fix non-empty lines
                                    fixed_text = ' ' * content_indent + text_line.strip()
                                    fixed_lines.append(fixed_text)
                                else:
                                    fixed_lines.append(text_line)
                            
                            # Fix closing tag indentation to match opening tag
                            closing_line = lines[closing_tag_line]
                            if closing_line.strip():
                                fixed_closing = ' ' * opening_indent + closing_line.strip()
                                fixed_lines.append(fixed_closing)
                            else:
                                fixed_lines.append(closing_line)
                            
                            i = closing_tag_line + 1
                            continue
            
            fixed_lines.append(line)
            i += 1
        
        fixed_content = '\n'.join(fixed_lines)
        
        # Only write if content changed
        if fixed_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
                
    except Exception as e:
        print(f"⚠️  Warning: Could not fix mixed content indentation in {file_path}: {e}")


def _clean_empty_lines(file_path: Path) -> None:
    """Remove lines that only contain whitespace (likely removed comments)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove lines that only contain whitespace and trailing whitespace from other lines
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            
            # If line only contains whitespace, skip it entirely (don't add to cleaned_lines)
            if stripped_line == '':
                continue  # Skip this line completely
            else:
                # Keep the line but remove trailing whitespace
                cleaned_lines.append(line.rstrip())
        
        cleaned_content = '\n'.join(cleaned_lines)
        
        # Only write if content changed
        if cleaned_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
                
    except Exception as e:
        print(f"⚠️  Warning: Could not clean empty lines in {file_path}: {e}")


def main():
    """Main function to format XML files using xmllint."""
    if len(sys.argv) < 2:
        print("Usage: python format_odoo_xml.py <xml_file> [xml_file2] ...")
        print("   or: python format_odoo_xml.py --all")
        print("")
        print("This formatter uses xmllint with the following features:")
        print("- Preserves XML comments")
        print("- 4-space indentation")
        print("- Proper Python expression spacing")
        return
    
    if sys.argv[1] == "--all":
        # Format all XML files in current directory and subdirectories
        xml_files = list(Path(".").rglob("*.xml"))
        print(f"Found {len(xml_files)} XML files to format with xmllint...")
    else:
        # Format specific files
        xml_files = [Path(f) for f in sys.argv[1:]]
    
    for xml_file in xml_files:
        if xml_file.exists():
            format_odoo_xml(xml_file)
        else:
            print(f"✗ File not found: {xml_file}")


if __name__ == "__main__":
    main()