# Group 15 submission

## Submission links

- [Group 15 artifacts folder](https://drive.google.com/drive/folders/1J8KbmClrJWQzPwq248O7B81_3NRtQGIK?usp=drive_link)
- [Whole-project demonstration video](https://drive.google.com/file/d/1-yIpgDq7lpkkwypf6Lnp9yAZhWEdek3l/view?usp=drive_link)
- [Source repository](https://github.com/I30398/BITS_API_Assignment1)

The final report is `report/cloud-review/15.docx`. It contains the supplied
links, all five members and their contributions, explanations, results and
application/provider screenshots from the verified cloud evidence.

## Required submission

The supplied Assignment I brief requires one member to upload a Word or PDF
report named `<groupid>.docx` or `<groupid>.pdf` to the submission portal.
For this group, upload `15.docx` (or an equivalent `15.pdf`). A Drive folder
link does not replace this portal upload. No separate member submissions
are required.

The brief also requires a video demonstrating the entire project, uploaded
to Google Drive in a group-named folder. The supplied video is already inside
`Group_15_API_Assignment1_Submission`. This finalization checked its metadata
and folder placement, not the recording's contents.

The brief states 30 October 2026 at 11:55 pm as the deadline. Check any later
faculty announcement separately.

## Suggested contents of the artifacts folder

| File | Status | Reason |
| --- | --- | --- |
| Existing demonstration MP4 | Required | Demonstrates the whole application; already in the folder. |
| `15.docx` | Recommended folder copy; required on the portal | Gives the evaluator one report with screenshots, explanations, contributions and resource links. |
| `Group15_Assignment1_Presentation.pptx` | Optional | Summarizes architecture, EDA, model results and cloud evidence in 15 slides. |
| `Group15_Source_and_Evidence.zip` | Optional | Preserves runnable source, setup instructions, the dataset and the frozen cloud evidence independently of later repository changes. |

Slides and a source archive are supporting recommendations, not additional
requirements stated in the supplied brief. The report already embeds the
important screenshots, so a separate loose screenshot folder is unnecessary.
Keep the recording script, older review reports, transfer utilities, local
environments, runtime databases and work-state notes outside the submission.

## Access check

Drive metadata on 30 October 2026 showed only owner permissions for the folder
and video. Before submitting, grant the evaluator Viewer access, or enable
Anyone with the link as Viewer if permitted by the BITS account policy. Check
both the folder and the video from an account without owner access. Sharing
settings were not changed during document finalization.

## Regenerate the report

```bash
python -m src.generate_report \
  --snapshot-root evidence/cloud-prayogshala-20261026 \
  --output-dir report/cloud-review
```

The generation validates the frozen evidence inventory and screenshot hashes.
Render and inspect the newly generated document before replacing the submitted
copy. Earlier reports remain historical records of their respective runs.
