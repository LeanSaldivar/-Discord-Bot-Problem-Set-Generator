import matplotlib.pyplot as plt
import matplotlib
import io
import re

# Configure matplotlib to use LaTeX rendering
matplotlib.rcParams['text.usetex'] = False  # Use mathtext, not full LaTeX
matplotlib.rcParams['mathtext.fontset'] = 'cm'  # Computer Modern font

def extract_latex(text):
    """Extract LaTeX equations from text marked with $$ ... $$"""
    pattern = r'\$\$(.*?)\$\$'
    matches = re.findall(pattern, text, re.DOTALL)
    return matches

def clean_latex_for_matplotlib(latex_str):
    """Clean LaTeX string to be compatible with matplotlib's mathtext parser."""
    # Remove unsupported commands
    unsupported_commands = [
        r'\Big', r'\big', r'\Bigg', r'\bigg',
        r'\left', r'\right',
        r'\displaystyle', r'\textstyle',
        r'\quad', r'\qquad',
    ]

    for cmd in unsupported_commands:
        latex_str = latex_str.replace(cmd, '')

    # Replace \text{...} with \mathrm{...} (more compatible)
    latex_str = re.sub(r'\\text\{([^}]*)\}', r'\\mathrm{\1}', latex_str)

    # Replace common spacing commands
    latex_str = latex_str.replace(r'\,', ' ')
    latex_str = latex_str.replace(r'\:', ' ')
    latex_str = latex_str.replace(r'\;', ' ')

    return latex_str.strip()

def render_all_latex_to_image(latex_equations):
    """Renders multiple LaTeX equations to a single image buffer."""
    if not latex_equations:
        return None

    num_equations = len(latex_equations)
    height_per_equation = 1.5
    total_height = max(2, num_equations * height_per_equation)

    fig = plt.figure(figsize=(10, total_height))
    rendered_count = 0

    for i, equation in enumerate(latex_equations):
        # Clean equation
        latex_clean = equation.strip()
        if latex_clean.startswith('$$') and latex_clean.endswith('$$'):
            latex_clean = latex_clean[2:-2].strip()

        # Clean for matplotlib compatibility
        latex_clean = clean_latex_for_matplotlib(latex_clean)

        try:
            # Calculate vertical position (from top to bottom)
            y_pos = 1 - (rendered_count + 0.5) / num_equations
            fig.text(0.5, y_pos, f"${latex_clean}$", ha='center', va='center', fontsize=18)
            rendered_count += 1
        except Exception as e:
            print(f"Skipping equation due to error: {e}")
            print(f"Problematic equation: {latex_clean[:100]}")
            continue

    if rendered_count == 0:
        plt.close(fig)
        return None

    plt.axis('off')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.2, dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf