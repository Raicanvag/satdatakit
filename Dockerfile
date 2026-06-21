# SatDataKit Docker Environment
# Author: Rafael Cañete Vazquez
# License: MIT

FROM continuumio/miniconda3:24.1.2-0

LABEL maintainer="Rafael Cañete Vazquez <rafael@satdatakit.dev>"
LABEL description="SatDataKit - Unified satellite data analysis toolkit"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ libgdal-dev gdal-bin libnetcdf-dev \
    libhdf5-dev libgeos-dev libproj-dev libspatialindex-dev \
    git wget curl && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN conda create -n satdatakit python=3.11 -y && \
    conda run -n satdatakit conda install -c conda-forge \
    gdal=3.8 rasterio=1.3 xarray=2024.1 rioxarray=0.15 \
    netcdf4=1.6 h5py=3.10 geopandas=0.14 shapely=2.0 \
    pyproj=3.6 pandas=2.1 numpy=1.26 scipy=1.11 matplotlib=3.8 \
    pillow=10.1 jupyterlab=4.0 pytest=7.4 black=23.12 ruff=0.1 \
    mypy=1.7 -y && conda clean -afy

ENV PATH="/opt/conda/envs/satdatakit/bin:$PATH"
RUN echo "conda activate satdatakit" >> ~/.bashrc

WORKDIR /workspace
COPY . /workspace/
RUN pip install -e ".[dev]"

RUN useradd -m -u 1000 satuser && chown -R satuser:satuser /workspace
USER satuser

EXPOSE 8888
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
