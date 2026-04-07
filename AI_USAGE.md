

No in-app AI, chatbot, LLM, or OpenAI features were implemented in this project.

AI tools were used only for coding assistance during development.

Final checks and submission review were completed manually.


Detailed prompts used during development

- Initial project generation

Prompt:
Build a complete Streamlit coursework project for data wrangling and visualization. The app must support CSV, XLSX, and JSON file upload, and it must be structured as a multipage application. Create separate pages for Home, Upload & Overview, Cleaning & Preparation, Visualization Builder, and Export & Report. The app should allow users to inspect dataset shape, data types, missing values, duplicates, and preview rows. It should also support missing value handling, duplicate removal, type conversion, categorical cleaning, numeric scaling, validation checks, visualizations, and export of both the cleaned dataset and a transformation report. Keep the implementation coursework-oriented, practical, and fully functional without adding any in-app AI, chatbot, LLM, or OpenAI features.

⸻

- Shared utilities and project structure

Prompt:
Scaffold the project in a clean modular way instead of putting everything into one file. Create reusable utility modules for data loading, profiling, transformations, validation, plotting, and session state management. Use a structure with app.py, pages/, utils/, sample_data/, requirements.txt, README.md, and AI_USAGE.md. Make the project easy to maintain, easy to run locally, and suitable for Streamlit deployment. Keep the code readable and student-friendly, with straightforward logic and clear naming.

⸻

- Upload and overview page

Prompt:
Implement the Upload & Overview page for the Streamlit coursework app. It must support loading CSV, XLSX, and JSON files, as well as bundled sample datasets. After loading, show dataset preview, shape, number of columns, duplicate row count, missing cell count, column names, data types, and summary statistics. The goal is to let the user immediately understand the structure and quality of the uploaded dataset before performing transformations.

⸻

- Cleaning and preparation page

Prompt:
Implement the Cleaning & Preparation page as the main transformation workspace of the app. Include tools for handling missing values, removing duplicates, converting data types, cleaning categorical columns, scaling numeric features, performing column operations, and running simple validation checks. Each transformation should be applied to the working dataset, and the result should remain available to later pages such as visualization and export. The page must be practical, interactive, and suitable for demonstrating coursework requirements.

⸻

- Missing values and duplicates

Prompt:
Add detailed support for missing values and duplicates to the Streamlit app. For missing values, allow the user to inspect missing counts and percentages, choose columns, and apply strategies such as mean, median, mode, constant fill, forward fill, or backward fill. For duplicates, allow detection of full-row duplicates or duplicates by selected columns, and let the user remove them. Show before-and-after information so the effect of each step is visible.

⸻

- Categorical cleaning and scaling

Prompt:
Expand the cleaning tools to better support categorical and numeric preparation. Add categorical cleaning features such as trimming whitespace, standardizing capitalization, and applying mapping/replacement rules to inconsistent category labels. Also add numeric scaling such as Min-Max scaling and Z-score standardization for selected numeric columns. Keep the controls understandable and suitable for a coursework demo where the user needs to clearly show cleaning categories and normalizing numeric columns.

⸻

- Visualization page

Prompt:
Implement the Visualization Builder page so the user can create multiple chart types from the current cleaned dataset.
Support at least histogram, bar chart, scatter plot, line chart, box plot, and heatmap or correlation-based visualizations. Allow the user to select chart type, columns, optional grouping, and simple filtering or aggregation where relevant. Use matplotlib and keep the output suitable for a short coursework demonstration.

⸻

- Export and transformation report

Prompt:
Implement the Export & Report page so the user can download the cleaned dataset and a transformation report. Support CSV and Excel export for the cleaned data, and export a transformation report in a structured format such as JSON or Markdown summary. The report should describe what transformations were applied, in what order, and with what settings. This is needed to complete the full coursework workflow from upload to export.

⸻

- Runtime validation and testing

Prompt:
Use the terminal to validate the Streamlit coursework project end-to-end. Install dependencies if needed, run the app locally, check that all pages load, test loading of at least one sample dataset, apply one missing-value cleaning step, one categorical cleaning step, one numeric scaling step, and generate several visualizations. Then verify that export and report download functions are available. If bugs or coursework mismatches are found, fix them directly and summarize what was changed.

⸻

- Final coursework polish

Prompt:
Review the current project and perform a final coursework-oriented polish pass. Keep the app simple and suitable for academic submission. Improve naming, wording, page presentation, and consistency where the project looks raw or autogenerated. Do not redesign the architecture or add unnecessary features. Focus on making the app clearer, more natural, and more presentable while preserving existing functionality.

⸻

- Submission cleanup

Prompt:
Prepare the Streamlit coursework project for final submission. Rewrite README.md into a short practical document with run instructions and a note about recreating .venv if the project folder was moved. Rewrite AI_USAGE.md in a short honest format. Remove development leftovers such as .venv, pycache, and log files. Add or update .gitignore to exclude temporary files. Make sure the app still runs after cleanup.

⸻

- Home page rendering fix

Prompt:
The Home page is incorrectly showing raw HTML tags such as <article>, <section>, and <div> as visible text in the browser. Fix only the Home page rendering issue. Either render the existing HTML correctly using st.markdown(..., unsafe_allow_html=True) or replace the broken sections with clean native Streamlit layout. Keep the Home page visually polished, natural, and appropriate for a coursework project.

⸻

- Environment and setup troubleshooting

Prompt:
Help troubleshoot local environment and launch issues for this Streamlit project. Check the Python version, verify whether the virtual environment is valid, explain how to recreate .venv if the folder path changed, reinstall requirements, and provide the correct command sequence to run app.py. Focus on practical setup fixes rather than changing the app itself.

⸻

- Deployment preparation

Prompt:
Review the project so it is ready for deployment on Streamlit Community Cloud. Make sure the repository contains the correct entrypoint file, valid requirements, sample data, and a clean project structure. Keep the app compatible with Python 3.12 and avoid anything that would break a basic Streamlit Cloud deployment.

⸻

AI-assisted tasks:
 project scaffolding
 page generation
 cleaning feature implementation
 visualization feature implementation
 export/report generation
 runtime bug fixing
 environment troubleshooting
 submission cleanup