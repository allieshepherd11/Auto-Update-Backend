Function arpsRate(qi, di, b, t)
    If b = 0 Then
        arpsRate = qi * Exp(-di * t)
    Else
        arpsRate = qi / (1 + b * di * t) ^ (1 / b)
    End If
End Function

Function cumlProd(qi, di, b, q)
    If b = 1 Then
        cumlProd = qi / di * Log(qi / q)
    Else
        cumlProd = qi ^ b / (di * (1 - b)) * (qi ^ (1 - b) - q ^ (1 - b))
    End If
End Function

Function nomDecline(di, b, t)
    nomDecline = di / (1 + b * di * t)
End Function

Function arpsWrapper(qi, di, b, t, startTime)
    If t >= startTime Then
        arpsWrapper = arpsRate(qi, di, b, t - startTime)
    Else
        arpsWrapper = 0
    End If
End Function
