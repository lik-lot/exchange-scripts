package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

type ScriptResult struct {
	Name     string
	Success  bool
	Duration time.Duration
	Error    error
	Output   string
}

func runPythonScript(scriptPath string, wg *sync.WaitGroup, results chan<- ScriptResult) {
	defer wg.Done()

	start := time.Now()
	scriptName := filepath.Base(scriptPath)
	scriptName = strings.TrimSuffix(scriptName, ".py")

	fmt.Printf("Starting %s...\n", scriptName)

	cmd := exec.Command("python3", scriptPath)
	cmd.Dir = filepath.Dir(scriptPath)

	output, err := cmd.CombinedOutput()
	duration := time.Since(start)

	result := ScriptResult{
		Name:     scriptName,
		Success:  err == nil,
		Duration: duration,
		Error:    err,
		Output:   string(output),
	}

	if err == nil {
		fmt.Printf("✓ %s completed in %v\n", scriptName, duration)
	} else {
		fmt.Printf("✗ %s failed in %v: %v\n", scriptName, duration, err)
	}

	results <- result
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

	fmt.Printf("Starting parallel execution of %d Python scripts...\n", len(pythonScripts))
	fmt.Println("=" + strings.Repeat("=", 60))

	var wg sync.WaitGroup
	results := make(chan ScriptResult, len(pythonScripts))

	startTime := time.Now()

	for _, script := range pythonScripts {
		scriptPath := filepath.Join(scriptDir, script)
		if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
			fmt.Printf("⚠ Skipping %s (file not found)\n", script)
			continue
		}

		wg.Add(1)
		go runPythonScript(scriptPath, &wg, results)
	}

	wg.Wait()
	close(results)

	totalDuration := time.Since(startTime)

	fmt.Println("\n" + strings.Repeat("=", 60))
	fmt.Printf("Execution Summary (Total time: %v)\n", totalDuration)
	fmt.Println(strings.Repeat("=", 60))

	successful := 0
	failed := 0

	var failedScripts []ScriptResult

	for result := range results {
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
