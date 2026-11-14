export function extractDiabetesFromText(text, currentData) {
  const rawLines = text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const normalized = rawLines.join(" ").toLowerCase().replace(/\s+/g, " ").trim();
  const nextData = { ...currentData };
  const fields = [];

  const escapeRegex = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  const valueAfterLabel = (labels, minimum, maximum) => {
    for (const label of labels) {
      const labelPattern = escapeRegex(label);
      const regex = new RegExp(`${labelPattern}(?:\\s+(?:level|value|reading|result|mg|mmhg|percent|%))?\\s*(?:[:=]|-)?\\s*(\\d+(?:\\.\\d+)?)`, "i");
      const match = normalized.match(regex);
      if (!match) continue;
      const value = Number(match[1]);
      if (Number.isFinite(value) && value >= minimum && value <= maximum) return value;
    }
    return null;
  };

  const valueAfterLabelText = (labels, options) => {
    const orderedOptions = [...options].sort((a, b) => b.length - a.length);
    for (const label of labels) {
      const labelPattern = escapeRegex(label);
      const regex = new RegExp(`${labelPattern}\\s*(?:[:=]|-)?\\s*(?:${orderedOptions.map((option) => escapeRegex(option)).join("|")})`, "i");
      const match = normalized.match(regex);
      if (match) return match[0].replace(new RegExp(`^.*?${labelPattern}\\s*(?:[:=]|-)?\\s*`, "i"), "").trim();
    }
    return null;
  };

  const yesNoAfterLabel = (labels) => {
    for (const label of labels) {
      const labelPattern = escapeRegex(label);
      const regex = new RegExp(`${labelPattern}\\s*(?:[:=]|-)?\\s*(yes|no|positive|negative|present|absent|y|n)`, "i");
      const match = normalized.match(regex);
      if (!match) continue;
      const value = match[1].toLowerCase();
      return ["yes", "y", "positive", "present"].includes(value) ? 1 : 0;
    }
    return null;
  };

  const patientName = (() => {
    const direct = rawLines.findIndex((line) => /patient\s+name/i.test(line));
    if (direct >= 0) {
      const nameLineIndex = direct + 1;
      if (rawLines[nameLineIndex]) {
        const name = rawLines[nameLineIndex].replace(/\s+/g, " ").trim();
        if (name && !/^(age|gender|patient\s+id)$/i.test(name)) return name;
      }
    }

    const patientMatch = normalized.match(/patient\s+name\s+([a-z]+(?:\s+[a-z]+){0,5})(?=\s+(?:age|gender|patient\s+id|hypertension|smoking|bmi|hba1c|blood\s+glucose))/i);
    return patientMatch ? patientMatch[1].replace(/\b\w/g, (letter) => letter.toUpperCase()) : "";
  })();

  const setNumber = (field, value) => {
    if (value !== null) { nextData[field] = value; fields.push(field); }
  };

  setNumber("age", valueAfterLabel(["age"], 1, 120));
  setNumber("bmi", valueAfterLabel(["bmi", "body mass index"], 10, 80));
  setNumber("HbA1c_level", valueAfterLabel(["hba1c", "a1c", "glycated hemoglobin", "ha1c"], 2, 20));
  setNumber("blood_glucose_level", valueAfterLabel(["fasting blood glucose", "fasting glucose", "blood glucose", "blood sugar", "glucose level", "random blood glucose", "random blood sugar"], 20, 700));

  const hypertension = yesNoAfterLabel(["hypertension", "htn"]);
  const heartDisease = yesNoAfterLabel(["heart disease", "heart-disease", "cardiac disease", "cardiovascular disease"]);
  if (hypertension !== null) { nextData.hypertension = hypertension; fields.push("hypertension"); }
  if (heartDisease !== null) { nextData.heart_disease = heartDisease; fields.push("heart_disease"); }

  const genderValue = valueAfterLabelText(["gender", "sex"], ["female", "male", "other"]);
  if (genderValue) {
    const gender = genderValue.toLowerCase().replace(/[^a-z]/g, "");
    nextData.gender = gender.charAt(0).toUpperCase() + gender.slice(1);
    fields.push("gender");
  }

  const smokingValue = valueAfterLabelText(["smoking history", "smoking", "tobacco use"], ["no info", "never", "former", "current", "not current", "ever", "yes", "no", "former smoker", "current smoker"]);
  if (smokingValue) {
    const normalizedSmoking = smokingValue.toLowerCase().replace(/\s+/g, " ").replace(/[^a-z\s]/g, "");
    nextData.smoking_history = normalizedSmoking === "no info"
      ? "No Info"
      : normalizedSmoking === "no" || normalizedSmoking === "never" || normalizedSmoking === "non smoker" ? "never"
      : normalizedSmoking === "yes" || normalizedSmoking === "current smoker" ? "current"
      : normalizedSmoking === "former smoker" ? "former"
      : normalizedSmoking;
    fields.push("smoking_history");
  }

  return { nextData, patientName, fields: [...new Set(fields)] };
}
