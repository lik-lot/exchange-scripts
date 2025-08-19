package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

type ScriptResult struct {
	Name     string
	Success  bool
	Duration time.Duration
	Error    error
	Output   string
}

func runPythonScript(scriptPath string, current int, total int) ScriptResult {
	start := time.Now()
	scriptName := filepath.Base(scriptPath)
	scriptName = strings.TrimSuffix(scriptName, ".py")

	progress := float64(current) / float64(total) * 100
	fmt.Printf("🔄 [%d/%d - %.1f%%] Starting %s...\n", current, total, progress, scriptName)
	fmt.Printf("📋 Output from %s:\n", scriptName)
	fmt.Println(strings.Repeat("-", 40))

	cmd := exec.Command("python3", scriptPath)
	cmd.Dir = filepath.Dir(scriptPath)
	
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	err := cmd.Run()
	duration := time.Since(start)

	result := ScriptResult{
		Name:     scriptName,
		Success:  err == nil,
		Duration: duration,
		Error:    err,
		Output:   "",
	}

	fmt.Println(strings.Repeat("-", 40))
	if err == nil {
		fmt.Printf("✓ [%d/%d - %.1f%%] %s completed in %v\n", current, total, progress, scriptName, duration)
	} else {
		fmt.Printf("✗ [%d/%d - %.1f%%] %s failed in %v: %v\n", current, total, progress, scriptName, duration, err)
	}

	return result
}

func main() {
	scriptDir := "."
	if len(os.Args) > 1 {
		scriptDir = os.Args[1]
	}

	pythonScripts := []string{
		"biconomy.py",
		"bigone.py",
		"binance.py",
		"bitget.py",
		"bitmart.py",
		"bitrue.py",
		"btse.py",
		"bybit.py",
		"coinbase.py",
		"coinex.py",
		"coinw.py",
		"cryptocom.py",
		"deepcoin.py",
		"digifinex.py",
		"gateio.py",
		"gemini.py",
		"hashkeyglobal.py",
		"htx.py",
		"kraken.py",
		"kucoin.py",
		"lbank.py",
		"mexc.py",
		"okx.py",
		"pionex.py",
		"toobit.py",
		"whitebit.py",
	}

	validScripts := []string{}
	for _, script := range pythonScripts {
		scriptPath := filepath.Join(scriptDir, script)
		if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
			fmt.Printf("⚠ Skipping %s (file not found)\n", script)
			continue
		}
		validScripts = append(validScripts, script)
	}

	fmt.Printf("Starting sequential execution of %d Python scripts...\n", len(validScripts))
	fmt.Println("=" + strings.Repeat("=", 60))

	startTime := time.Now()
	var results []ScriptResult

	for i, script := range validScripts {
		scriptPath := filepath.Join(scriptDir, script)
		result := runPythonScript(scriptPath, i+1, len(validScripts))
		results = append(results, result)
		
		if i < len(validScripts)-1 {
			fmt.Println()
		}
	}

	totalDuration := time.Since(startTime)

	fmt.Println("\n" + strings.Repeat("=", 60))
	fmt.Printf("Execution Summary (Total time: %v)\n", totalDuration)
	fmt.Println(strings.Repeat("=", 60))

	successful := 0
	failed := 0
	var failedScripts []ScriptResult

	for _, result := range results {
		if result.Success {
			fmt.Printf("✓ %-15s - %v\n", result.Name, result.Duration)
			successful++
		} else {
			fmt.Printf("✗ %-15s - %v (ERROR)\n", result.Name, result.Duration)
			failedScripts = append(failedScripts, result)
			failed++
		}
	}

	fmt.Println(strings.Repeat("-", 60))
	fmt.Printf("Results: %d successful, %d failed\n", successful, failed)

	if len(failedScripts) > 0 {
		fmt.Println("\nFailed Scripts Details:")
		fmt.Println(strings.Repeat("-", 60))
		for _, result := range failedScripts {
			fmt.Printf("\n%s:\n", result.Name)
			fmt.Printf("Error: %v\n", result.Error)
			if len(result.Output) > 0 {
				fmt.Printf("Output:\n%s\n", result.Output)
			}
		}
	}

	if failed > 0 {
		os.Exit(1)
	}
}
