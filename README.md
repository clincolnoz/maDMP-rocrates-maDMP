# maDMP-rocrates-maDMP
[![DOI](https://zenodo.org/badge/275586451.svg)](https://zenodo.org/badge/latestdoi/275586451)


## Task description

RO-Crate[5][5]
is a community effort to establish a lightweight approach to packaging research data with
their metadata. It is based on schema.org annotations in JSON-LD, and aims to make best-practice in
formal metadata description accessible and practical for use in a wider variety of situations, from an
individual researcher working with a folder of data, to large data-intensive computational research
environments.
Machine-actionable DMPs[6][6]
(maDMPs) are an emerging standard for exchange of DMPs between
systems involved in research data management. There are certain overlaps in the scope of maDMPs
and ro-crates. Reuse and transfer of information between the maDMPs and ro-crates can facilitate
adoption of both and reduce workload imposed on researchers to document their data.
In this task you will:
- Define a mapping between ro-crate 1.0 and maDMPs
- Develop a tool that
  - Extracts relevant information from an maDMP and creates ro-crates [1 to many]
  - Reuses information from ro-crates to generate a maDMP [many to 1]
To test your mapping and the tool, you will:
- Extract information from maDMPs to create ro-crates
  - 5 selected maDMPs from the Data Stewardship community[7]
  - 5 examples from the RDA Repository[8]
(must include ex9-dmp-long)
- Use information from ro-crates to fill in maDMPs
  - 3 example RO-crates from the official ro-crate website
  - 2 realistic examples of RO-crates created by you to test the coverage of your mapping
Don’t forget to validate the generated maDMPs against the provided JSON schema. The mapping must
be as complete as possible.

[5]: <https://researchobject.github.io/ro-crate/>  
[6]: https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard  
[7]: https://zenodo.org/communities/tuw-dmps-ds-2020/  
[8]: https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard/tree/master/examples/JSON  