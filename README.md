# potato-dt

## purpose 
A lightweight **digital twin prototype** for simulating potato growth in controlled environments (like greenhouses or spacerafts). 
Built with **Python + Streamlit**, this model integrates a biophysical crop growth model with a thermal model of the chamber to estimate biomass accumulation, tuber formation, and energy use under different light, CO₂, and temperatures levels to explore sustainable food production for Mars missions.

## model-structure 

### Dependant (measurable) variables:

1. Leaf, stem, and tuber dry mass

2. Thermal time accumulation (for phenology)

3. Chamber temperature

4. Cumulative energy consumption

### Independant (modifiable) variables:  

1. Environmental modifiers: calculate how temperature and CO₂ affect photosynthesis.

2. Light interception: determine what fraction of incoming radiation is absorbed by the canopy.

3. Photosynthetic production: convert absorbed light into biomass using a light-use-efficiency (LUE) model.

4. Respiration: subtract maintenance costs from total biomass.

5. Partitioning: distribute new biomass among leaves, stems, and tubers.

6. Thermal balance: compute the next day's chamber temperature from heat inputs and cooling. 

## key equations

Daily Light Integral (DLI): 

<img width="350" height="71" alt="Screenshot 2025-10-06 at 4 51 23 PM" src="https://github.com/user-attachments/assets/3f760ca1-70c1-40c5-9a58-70f5550e1f1f" />

Light-Use Efficiency (LUE) Model

<img width="439" height="54" alt="Screenshot 2025-10-06 at 4 51 43 PM" src="https://github.com/user-attachments/assets/aa21a48c-d560-4e0a-9d76-64fadc30953d" />

Canopy Light Interception (Beer–Lambert Law)

<img width="180" height="61" alt="Screenshot 2025-10-06 at 4 51 55 PM" src="https://github.com/user-attachments/assets/cc9b090c-fde2-43b8-b9f2-db985fb9a41c" />
<img width="173" height="47" alt="Screenshot 2025-10-06 at 4 52 13 PM" src="https://github.com/user-attachments/assets/c0c7c6aa-2fb6-4cf7-b23d-2c3e1852fee9" />

Thermal Time (Phenology) 

<img width="313" height="54" alt="Screenshot 2025-10-06 at 4 52 21 PM" src="https://github.com/user-attachments/assets/51583681-626a-445b-bbe7-be630b20683b" />

Tuber Partitioning 

<img width="377" height="46" alt="Screenshot 2025-10-06 at 4 52 35 PM" src="https://github.com/user-attachments/assets/9494650f-54bb-4e92-aa23-77cd07f0c31d" />

Chamber Temperature Step

<img width="299" height="65" alt="Screenshot 2025-10-06 at 4 52 43 PM" src="https://github.com/user-attachments/assets/dcd3c4a6-a857-4f1d-91dc-b6906f1e7cf8" />

---

## quickstart
```bash
git clone https://github.com/<your-username>/mars-potato-digital-twin.git
cd mars-potato-digital-twin
pip install -r requirements.txt
streamlit run app/app_potato.py
