import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
import pickle
import os

class DriverLSTM(nn.Module):
    def __init__(self, input_size=3, hidden_size=64, num_layers=2):
        super(DriverLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, input_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out

def prepare_sequences(data: list, seq_length: int = 5):
    sequences = []
    targets = []
    for i in range(len(data) - seq_length):
        seq = data[i:i + seq_length]
        target = data[i + seq_length]
        sequences.append(seq)
        targets.append(target)
    return np.array(sequences), np.array(targets)

def train_model(locations: list):
    if len(locations) < 20:
        return None, None, "Not enough data — need at least 20 location updates"

    raw = np.array([
        [loc["latitude"], loc["longitude"], loc["speed"]]
        for loc in locations
    ], dtype=np.float32)

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(raw)

    SEQ_LENGTH = 5
    X, y = prepare_sequences(scaled, SEQ_LENGTH)

    X_tensor = torch.FloatTensor(X)
    y_tensor = torch.FloatTensor(y)

    model = DriverLSTM(input_size=3, hidden_size=64, num_layers=2)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    model.train()
    for epoch in range(100):
        optimizer.zero_grad()
        output = model(X_tensor)
        loss = criterion(output, y_tensor)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 20 == 0:
            print(f"Epoch {epoch+1}/100, Loss: {loss.item():.6f}")

    torch.save(model.state_dict(), "lstm_model.pth")
    with open("scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    return model, scaler, "Model trained successfully"

def predict_anomalies(locations: list):
    if not os.path.exists("lstm_model.pth"):
        return [], "Model not trained yet — call /train/{driver_id} first"

    with open("scaler.pkl", "rb") as f:
        scaler = pickle.load(f)

    raw = np.array([
        [loc["latitude"], loc["longitude"], loc["speed"]]
        for loc in locations
    ], dtype=np.float32)

    scaled = scaler.transform(raw)

    SEQ_LENGTH = 5
    model = DriverLSTM(input_size=3, hidden_size=64, num_layers=2)
    model.load_state_dict(torch.load("lstm_model.pth", weights_only=True))
    model.eval()

    anomalies = []
    THRESHOLD = 0.02

    with torch.no_grad():
        for i in range(len(scaled) - SEQ_LENGTH):
            seq = torch.FloatTensor(scaled[i:i + SEQ_LENGTH]).unsqueeze(0)
            predicted = model(seq).numpy()[0]
            actual = scaled[i + SEQ_LENGTH]
            error = np.mean((predicted - actual) ** 2)

            if error > THRESHOLD:
                loc = locations[i + SEQ_LENGTH]
                anomalies.append({
                    "record_id": loc["id"],
                    "driver_id": loc["driver_id"],
                    "timestamp": str(loc["timestamp"]),
                    "latitude": loc["latitude"],
                    "longitude": loc["longitude"],
                    "speed": loc["speed"],
                    "reconstruction_error": round(float(error), 6),
                    "type": "lstm_anomaly"
                })

    return anomalies, "OK"