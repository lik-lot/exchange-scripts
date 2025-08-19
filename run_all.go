package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

type ScriptResult struct {
	Name     string
	Success  bool
	Duration time.Duration
	Error    error
	Output   string
}

func runPythonScript(scriptPath string, wg *sync.WaitGroup, results chan<- ScriptResult, completed *int64, total int) {
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

	completedCount := atomic.AddInt64(completed, 1)
	progress := float64(completedCount) / float64(total) * 100

	if err == nil {
		fmt.Printf("✓ %s completed in %v [%d/%d - %.1f%%]\n", scriptName, duration, completedCount, total, progress)
	} else {
		fmt.Printf("✗ %s failed in %v: %v [%d/%d - %.1f%%]\n", scriptName, duration, err, completedCount, total, progress)
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
	var completed int64 = 0

	validScripts := 0
	for _, script := range pythonScripts {
		scriptPath := filepath.Join(scriptDir, script)
		if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
			fmt.Printf("⚠ Skipping %s (file not found)\n", script)
			continue
		}
		validScripts++
	}

	startTime := time.Now()

	for _, script := range pythonScripts {
		scriptPath := filepath.Join(scriptDir, script)
		if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
			continue
		}

		wg.Add(1)
		go runPythonScript(scriptPath, &wg, results, &completed, validScripts)
	}

	go func() {
		ticker := time.NewTicker(10 * time.Second)
		defer ticker.Stop()
		for range ticker.C {
			currentCompleted := atomic.LoadInt64(&completed)
			if currentCompleted < int64(validScripts) {
				elapsed := time.Since(startTime)
				progress := float64(currentCompleted) / float64(validScripts) * 100
				fmt.Printf("\n📊 Progress update: %d/%d completed (%.1f%%) - Elapsed: %v\n", currentCompleted, validScripts, progress, elapsed)
			} else {
				break
			}
		}
	}()

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
